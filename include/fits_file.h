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



#endif /* end of include guard: FITS_FILE_H */
