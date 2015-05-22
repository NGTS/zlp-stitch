#ifndef FITS_UPDATER_H

#define FITS_UPDATER_H

#include <map>
#include <string>
#include <set>
#include <vector>

#include "util.h"

struct FITSFile;

struct FitsUpdater {
    FitsUpdater(
        const ImageDimensions &dim,
        const std::map<std::string, ColumnDefinition> &imagelist_columns,
        const std::map<std::string, ColumnDefinition> &catalogue_columns,
        const std::set<std::string> image_names);
    ~FitsUpdater();

    void updateImagelist(FITSFile &f);
    void updateImages(FITSFile &f);
    void updateCatalogue(FITSFile &f);
    void render(const std::vector<std::string> &files,
                const std::string &output);

    FITSFile *outfile;
    ImageDimensions dimensions;
    std::map<std::string, ColumnDefinition> imagelist_columns;
    std::map<std::string, ColumnDefinition> catalogue_columns;
    std::set<std::string> image_names;
    int currentImage;
};

#endif /* end of include guard: FITS_UPDATER_H */
