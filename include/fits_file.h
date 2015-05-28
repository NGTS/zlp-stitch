#ifndef FITS_FILE_H

#define FITS_FILE_H

#include <fitsio.h>
#include <string>
#include <map>
#include <vector>

#include "util.h"

struct FITSFile {
    fitsfile *fptr;
    int status;
    std::string filename;

    FITSFile(fitsfile *fptr, int status) : fptr(fptr), status(status) {}
    FITSFile(fitsfile *fptr) : FITSFile(fptr, 0) {}
    FITSFile() : FITSFile(NULL) {}

    static FITSFile *createFile(const std::string &filename);

    FITSFile(const std::string &filename);
    ~FITSFile() { close(); }

    ImageDimensions imageDimensions();
    MJDRange mjd_range();
    int colnum(const std::string &name);
    long nimages();

    std::vector<double> readWholeImage();
    void writeImageSubset(const std::vector<double> &data, long start_image,
                          const ImageDimensions &dim);

    std::vector<std::pair<std::string, ColumnDefinition>> column_description();

    void addImage(const std::string &name, long nimages, long napertures);
    void addImage(const std::string &name, const ImageDimensions &dim) {
        addImage(name, dim.nimages, dim.napertures);
    };
    void addBinaryTable(
        const std::string &name,
        const std::map<std::string, ColumnDefinition> &column_description,
        long nrows);

    void toHDU(const std::string &name);
    void toHDU(int index);
    void close();
    void check();
};

template <typename T>
std::vector<T> readColumn(FITSFile &f, long nrows, int colnum);

template <typename T>
void writeColumn(FITSFile *f, std::vector<T> &data, long start, int colnum);

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
                       int source_colnum, int dest_colnum,
                       const ColumnDefinition &defs);

#endif /* end of include guard: FITS_FILE_H */
