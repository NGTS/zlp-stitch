#include "fits_file.h"
#include <vector>
#include <stdexcept>
#include <iostream>
#include <map>
#include <valarray>
#include <sstream>
#include <algorithm>

#include "time_utils.h"


using namespace std;

FITSFile::FITSFile(const string &filename) : FITSFile() {
    this->filename = filename;
    fits_open_file(&fptr, filename.c_str(), READONLY, &status);
    check();
}

FITSFile *FITSFile::createFile(const string &filename) {
    stringstream ss;
    ss << "!" << filename;

    FITSFile *f = new FITSFile();
    f->filename = filename;
    fits_create_file(&f->fptr, ss.str().c_str(), &f->status);
    f->check();

    /* Add empty primary */
    fits_write_imghdr(f->fptr, 8, 0, NULL, &f->status);
    f->check();
    return f;
}

MJDRange FITSFile::mjd_range() {
    long nrows = nimages();
    vector<double> mjd(nrows);
    toHDU("IMAGELIST");

    fits_read_col(fptr, TDOUBLE, colnum("TMID"), 1, 1, nrows, NULL, &mjd[0],
                  NULL, &status);
    check();

    MJDRange out;
    auto minmax_values = minmax_element(mjd.begin(), mjd.end());
    out.min = *minmax_values.first;
    out.max = *minmax_values.second;
    return out;
}

void FITSFile::close() {
    if (fptr) {
        fits_close_file(fptr, &status);
        check();
        fptr = NULL;
    }
}

void FITSFile::check() {
    if (status) {
        fits_report_error(stderr, status);
        exit(status);
    }
}

void FITSFile::toHDU(const string &name) {
    fits_movnam_hdu(fptr, ANY_HDU, (char *)name.c_str(), 0, &status);
}

void FITSFile::toHDU(int index) {
    fits_movabs_hdu(fptr, index + 1, NULL, &status);
}

int FITSFile::colnum(const string &name) {
    int colnum = -1;
    fits_get_colnum(fptr, CASEINSEN, (char *)name.c_str(), &colnum, &status);
    if (status == COL_NOT_FOUND) {
        status = 0;
        fits_clear_errmsg();
        return -1;
    } else {
        return colnum;
    }
}

ImageDimensions FITSFile::imageDimensions() {
    long naxes[2];
    fits_get_img_size(fptr, 2, naxes, &status);
    check();

    ImageDimensions out;
    out.nimages = naxes[0];
    out.napertures = naxes[1];
    return out;
}

void FITSFile::addImage(const string &name, long nimages, long napertures) {
    log << "Adding image " << name << endl;
    long naxes[] = {nimages, napertures};
    fits_create_img(fptr, DOUBLE_IMG, 2, naxes, &status);
    check();

    fits_write_key(fptr, TSTRING, "EXTNAME", (char *)name.c_str(), NULL,
                   &status);
    check();
}

vector<pair<string, ColumnDefinition>> FITSFile::column_description() {
    vector<pair<string, ColumnDefinition>> out;

    int ncols = 0;
    fits_get_num_cols(fptr, &ncols, &status);
    check();

    for (int i = 0; i < ncols; i++) {
        pair<string, ColumnDefinition> column;
        stringstream ss;
        ss << i + 1;
        char buf[80];
        int num;
        fits_get_colname(fptr, CASEINSEN, (char *)ss.str().c_str(), buf, &num,
                         &status);
        check();
        fits_get_coltype(fptr, i + 1, &column.second.type,
                         &column.second.repeat, &column.second.width, &status);
        check();

        column.first = buf;

        out.push_back(column);
    }

    return out;
}

void FITSFile::addBinaryTable(
    const string &name, const map<string, ColumnDefinition> &column_description,
    long nrows) {
    vector<char *> column_names(nrows), column_types(nrows);
    int i = 0;
    for (auto row : column_description) {
        column_names[i] = (char *)row.first.c_str();
        if (row.second.type == TSTRING) {
            stringstream ss;
            ss << row.second.width << "A";
            column_types[i] = (char *)ss.str().c_str();
        } else {
            switch (row.second.type) {
            case TDOUBLE:
                column_types[i] = "1D";
                break;
            case TLONGLONG:
                column_types[i] = "1K";
                break;
            case TLONG:
                column_types[i] = "1J";
                break;
            case TFLOAT:
                column_types[i] = "1E";
                break;
            case TLOGICAL:
                column_types[i] = "1L";
                break;
            case TSTRING:
                break;
            default:
                log << "No string conversion for column " << row.first
                     << ", type " << row.second.type << endl;
                break;
            }
        }
        i++;
    }
    fits_create_tbl(fptr, BINARY_TBL, nrows, column_description.size(),
                    &column_names[0], &column_types[0], NULL,
                    (char *)name.c_str(), &status);
    check();
}

long FITSFile::nimages() {
    long nrows = -1;
    toHDU("IMAGELIST");
    check();
    fits_get_num_rows(fptr, &nrows, &status);
    check();
    return nrows;
}

void addToBoolColumn(FITSFile &source, FITSFile *dest, long nrows, long start,
                     int source_colnum, int dest_colnum) {
    std::vector<int> data(nrows);
    fits_read_col(source.fptr, TLOGICAL, source_colnum, 1, 1, nrows, NULL,
                  &data[0], NULL, &source.status);
    if (source.status == COL_NOT_FOUND) {
        source.status = 0;
        fits_clear_errmsg();
    } else {
        source.check();
        fits_write_col(dest->fptr, TLOGICAL, dest_colnum, start + 1, 1,
                       data.size(), &data[0], &dest->status);
        dest->check();
    }
}

void addToStringColumn(FITSFile &source, FITSFile *dest, long nrows, long start,
                       int source_colnum, int dest_colnum,
                       const ColumnDefinition &defs) {
    valarray<char *> cptr(nrows);
    for (int i = 0; i < nrows; i++) {
        cptr[i] = new char[defs.width + 1];
    }
    fits_read_col_str(source.fptr, source_colnum, 1, 1, nrows, NULL, &cptr[0],
                      NULL, &source.status);
    if (source.status == COL_NOT_FOUND) {
        source.status = 0;
        fits_clear_errmsg();
    } else {
        source.check();
        fits_write_col(dest->fptr, TSTRING, dest_colnum, start + 1, 1, nrows,
                       &cptr[0], &dest->status);
        dest->check();
    }

    for (int i = 0; i < nrows; i++) {
        delete cptr[i];
    }
}

vector<double> FITSFile::readWholeImage() {
    ImageDimensions dim = imageDimensions();
    vector<double> out(dim.nimages * dim.napertures);
    long fpixel[] = {1, 1};
    long lpixel[] = {dim.nimages, dim.napertures};
    long inc[] = {1, 1};

    fits_read_subset(fptr, TDOUBLE, fpixel, lpixel, inc, NULL, &out[0], NULL,
                     &status);
    check();

    return out;
}

void FITSFile::writeImageSubset(const vector<double> &data, long start_image,
                                const ImageDimensions &dim) {
    long fpixel[] = {start_image + 1, 1};
    long lpixel[] = {start_image + dim.nimages, dim.napertures};
    fits_write_subset(fptr, TDOUBLE, fpixel, lpixel, (double *)&data[0],
                      &status);
    check();
}

template <>
std::vector<double> readColumn<double>(FITSFile &f, long nrows, int colnum) {
    std::vector<double> data(nrows);
    fits_read_col(f.fptr, TDOUBLE, colnum, 1, 1, nrows, NULL, &data[0], NULL,
                  &f.status);
    return data;
}

template <>
std::vector<float> readColumn<float>(FITSFile &f, long nrows, int colnum) {
    std::vector<float> data(nrows);
    fits_read_col(f.fptr, TFLOAT, colnum, 1, 1, nrows, NULL, &data[0], NULL,
                  &f.status);
    return data;
}

template <>
std::vector<int> readColumn<int>(FITSFile &f, long nrows, int colnum) {
    std::vector<int> data(nrows);
    fits_read_col(f.fptr, TINT, colnum, 1, 1, nrows, NULL, &data[0], NULL,
                  &f.status);
    return data;
}

template <>
std::vector<long> readColumn<long>(FITSFile &f, long nrows, int colnum) {
    std::vector<long> data(nrows);
    fits_read_col(f.fptr, TLONG, colnum, 1, 1, nrows, NULL, &data[0], NULL,
                  &f.status);
    return data;
}

template <>
void writeColumn(FITSFile *f, std::vector<double> &data, long start,
                 int colnum) {
    fits_write_col(f->fptr, TDOUBLE, colnum, start + 1, 1, data.size(),
                   &data[0], &f->status);
    f->check();
}

template <>
void writeColumn(FITSFile *f, std::vector<int> &data, long start, int colnum) {
    fits_write_col(f->fptr, TINT, colnum, start + 1, 1, data.size(), &data[0],
                   &f->status);
    f->check();
}

template <>
void writeColumn(FITSFile *f, std::vector<long> &data, long start, int colnum) {
    fits_write_col(f->fptr, TLONG, colnum, start + 1, 1, data.size(), &data[0],
                   &f->status);
    f->check();
}

template <>
void writeColumn(FITSFile *f, std::vector<float> &data, long start,
                 int colnum) {
    fits_write_col(f->fptr, TFLOAT, colnum, start + 1, 1, data.size(), &data[0],
                   &f->status);
    f->check();
}
