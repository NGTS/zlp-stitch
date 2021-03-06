#include "fits_updater.h"
#include <iostream>
#include <fitsio.h>

#include "fits_file.h"
#include "time_utils.h"

using namespace std;

FitsUpdater::FitsUpdater(const ImageDimensions &dim,
                         const map<string, ColumnDefinition> &imagelist_columns,
                         const map<string, ColumnDefinition> &catalogue_columns,
                         const set<string> image_names)
    : outfile(NULL), dimensions(dim), imagelist_columns(imagelist_columns),
      catalogue_columns(catalogue_columns), image_names(image_names),
      currentImage(0) {}

void FitsUpdater::updateImagelist(FITSFile &f) {
    outfile->toHDU("IMAGELIST");
    f.toHDU("IMAGELIST");
    long nrows = f.nimages();
    for (auto column : imagelist_columns) {
        int source_colnum = f.colnum(column.first);
        int dest_colnum = outfile->colnum(column.first);

        if (source_colnum == -1) {
            continue;
        }

        switch (column.second.type) {
        case TDOUBLE:
            addToColumn<double>(f, outfile, nrows, currentImage, source_colnum,
                                dest_colnum);
            break;
        case TFLOAT:
            addToColumn<float>(f, outfile, nrows, currentImage, source_colnum,
                               dest_colnum);
            break;
        case TINT:
            addToColumn<int>(f, outfile, nrows, currentImage, source_colnum,
                             dest_colnum);
            break;
        case TLONG:
            addToColumn<long>(f, outfile, nrows, currentImage, source_colnum,
                              dest_colnum);
            break;
        case TLONGLONG:
            addToColumn<long>(f, outfile, nrows, currentImage, source_colnum,
                              dest_colnum);
            break;
        case TLOGICAL:
            addToBoolColumn(f, outfile, nrows, currentImage, source_colnum,
                            dest_colnum);
            break;
        case TSTRING:
            addToStringColumn(f, outfile, nrows, currentImage, source_colnum,
                              dest_colnum, column.second);
            break;
        default:
            log << "Not implemented: " << column.first << " "
                 << column.second.type << endl;
            break;
        }
    }
}

void FitsUpdater::updateImage(FITSFile &f, const string &image) {
    outfile->toHDU(image);
    outfile->check();
    f.toHDU(image);
    if (f.status == BAD_HDU_NUM) {
        f.status = 0;
        fits_clear_errmsg();
    } else {
        log << "Copying image " << image << " from " << f.filename << endl;
        vector<double> imageData = f.readWholeImage();
        outfile->writeImageSubset(imageData, currentImage,
                                    f.imageDimensions());
    }
}

void FitsUpdater::updateImages(FITSFile &f) {
    for (auto image : image_names) {
        updateImage(f, image);
    }
}

void FitsUpdater::updateCatalogue(FITSFile &f) {
    int sourcecol = -1;
    f.toHDU("CATALOGUE");
    outfile->toHDU("CATALOGUE");
    for (auto col : catalogue_columns) {
        log << "Updating catalogue column " << col.first << endl;
        fits_get_colnum(f.fptr, CASEINSEN, (char *)col.first.c_str(),
                        &sourcecol, &f.status);
        if (f.status != COL_NOT_FOUND) {
            log << "Copying column information" << endl;
            int destcol = outfile->colnum(col.first);
            fits_copy_col(f.fptr, outfile->fptr, sourcecol, destcol, false,
                          &outfile->status);
            outfile->check();
        } else {
            f.status = 0;
            fits_clear_errmsg();
        }
    }
}

void FitsUpdater::render(const vector<string> &files, const string &output) {

    outfile = FITSFile::createFile(output);

    log << "Updating catalogue from first file: " << files[0] << endl;
    outfile->addBinaryTable("CATALOGUE", catalogue_columns,
                            dimensions.napertures);
    FITSFile first(files[0]);
    updateCatalogue(first);


    log << "Updating imagelist" << endl;
    outfile->addBinaryTable("IMAGELIST", imagelist_columns, dimensions.nimages);
    for (auto filename : files) {
        log << "Updating from " << filename << endl;
        FITSFile source(filename);
        updateImagelist(source);
        currentImage += source.nimages();
    }

    log << "Reading in data from images" << endl;
    for (auto name : image_names) {
        outfile->addImage(name, dimensions);
        for (auto filename : files) {
            FITSFile source(filename);
            updateImage(source, name);
        }
    }
}

FitsUpdater::~FitsUpdater() {
    if (outfile) {
        delete outfile;
    }
}
