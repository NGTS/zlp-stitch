#ifndef FITS_FILE_H

#define FITS_FILE_H

#include <fitsio.h>
#include <string>
#include <map>
#include <vector>

struct ImageDimensions {
    long nimages, napertures;
};

struct ColumnDefinition {
    long repeat, width;
    int type;
};

struct MJDRange {
    double min, max;
};

struct FITSFile {
    fitsfile *fptr;
    int status;

    FITSFile(fitsfile *fptr, int status) : fptr(fptr), status(status) {}
    FITSFile(fitsfile *fptr) : FITSFile(fptr, 0) {}
    FITSFile() : FITSFile(NULL) {}

    static FITSFile* createFile(const std::string &filename);

    FITSFile(const std::string &filename);
    ~FITSFile() { close(); }

    ImageDimensions imageDimensions();
    MJDRange mjd_range();
    int colnum(const std::string &name);
    long nimages();

    std::vector<double> readWholeImage();
    void writeImageSubset(const std::vector<double> &data, long start_image, const ImageDimensions &dim);

    std::vector<std::pair<std::string, ColumnDefinition> > column_description();

    void addImage(const std::string &name, long nimages, long napertures);
    void addImage(const std::string &name, const ImageDimensions &dim) {
        addImage(name, dim.nimages, dim.napertures);
    };
    void addBinaryTable(const std::string &name, const std::map<std::string, ColumnDefinition> &column_description, long nrows);

    void toHDU(const std::string &name);
    void toHDU(int index);
    void close();
    void check();
};

template<typename T>
std::vector<T> readColumn(FITSFile &f, long nrows, int colnum) {
}

template<>
std::vector<double> readColumn<double>(FITSFile &f, long nrows, int colnum) {
    std::vector<double> data(nrows);
    fits_read_col(f.fptr, TDOUBLE, colnum, 1, 1, nrows, NULL, &data[0], NULL, &f.status);
    return data;
}

template<>
std::vector<float> readColumn<float>(FITSFile &f, long nrows, int colnum) {
    std::vector<float> data(nrows);
    fits_read_col(f.fptr, TFLOAT, colnum, 1, 1, nrows, NULL, &data[0], NULL, &f.status);
    return data;
}

template<>
std::vector<int> readColumn<int>(FITSFile &f, long nrows, int colnum) {
    std::vector<int> data(nrows);
    fits_read_col(f.fptr, TINT, colnum, 1, 1, nrows, NULL, &data[0], NULL, &f.status);
    return data;
}

template<>
std::vector<long> readColumn<long>(FITSFile &f, long nrows, int colnum) {
    std::vector<long> data(nrows);
    fits_read_col(f.fptr, TLONG, colnum, 1, 1, nrows, NULL, &data[0], NULL, &f.status);
    return data;
}

template <typename T>
void writeColumn(FITSFile *f, std::vector<T> &data, long start, int colnum) {
}

template <>
void writeColumn(FITSFile *f, std::vector<double> &data, long start, int colnum) {
    fits_write_col(f->fptr, TDOUBLE, colnum, start + 1, 1, data.size(), &data[0], &f->status);
    f->check();
}

template <>
void writeColumn(FITSFile *f, std::vector<int> &data, long start, int colnum) {
    fits_write_col(f->fptr, TINT, colnum, start + 1, 1, data.size(), &data[0], &f->status);
    f->check();
}

template <>
void writeColumn(FITSFile *f, std::vector<long> &data, long start, int colnum) {
    fits_write_col(f->fptr, TLONG, colnum, start + 1, 1, data.size(), &data[0], &f->status);
    f->check();
}

template <>
void writeColumn(FITSFile *f, std::vector<float> &data, long start, int colnum) {
    fits_write_col(f->fptr, TFLOAT, colnum, start + 1, 1, data.size(), &data[0], &f->status);
    f->check();
}

template <typename T>
void addToColumn(FITSFile &source, FITSFile *dest, long nrows, long start,
        int source_colnum, int dest_colnum) {
    std::vector<T> data = readColumn<T>(source, nrows, source_colnum);
    if (source.status == COL_NOT_FOUND) {
        source.status = 0;
        fits_clear_errmsg();
    } else {
        source.check();
        writeColumn<T>(dest, data, start, dest_colnum);
    }
}


void addToBoolColumn(FITSFile &source, FITSFile *dest, long nrows, long start,
        int source_colnum, int dest_colnum);
void addToStringColumn(FITSFile &source, FITSFile *dest, long nrows, long start,
        int source_colnum, int dest_colnum, const ColumnDefinition &defs);


#endif /* end of include guard: FITS_FILE_H */
