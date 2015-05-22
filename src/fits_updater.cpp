#include "fits_updater.h"
#include <iostream>
#include <fitsio.h>

#include "fits_file.h"

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
            cout << "Not implemented: " << column.first << " "
                 << column.second.type << endl;
            break;
        }
    }
}

void FitsUpdater::updateImages(FITSFile &f) {
    for (auto image : image_names) {
        outfile->toHDU(image);
        outfile->check();
        f.toHDU(image);
        if (f.status == BAD_HDU_NUM) {
            f.status = 0;
            fits_clear_errmsg();
        } else {
            cout << "Copying image " << image << endl;
            vector<double> imageData = f.readWholeImage();
            outfile->writeImageSubset(imageData, currentImage,
                                      f.imageDimensions());
        }
    }
}

void FitsUpdater::updateCatalogue(FITSFile &f) {
    int sourcecol = -1;
    f.toHDU("CATALOGUE");
    outfile->toHDU("CATALOGUE");
    for (auto col : catalogue_columns) {
        fits_get_colnum(f.fptr, CASEINSEN, (char *)col.first.c_str(),
                        &sourcecol, &f.status);
        if (f.status != COL_NOT_FOUND) {
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
    outfile->addBinaryTable("IMAGELIST", imagelist_columns, dimensions.nimages);
    outfile->addBinaryTable("CATALOGUE", catalogue_columns,
                            dimensions.napertures);
    for (auto name : image_names) {
        outfile->addImage(name, dimensions);
    }

    FITSFile first(files[0]);
    updateCatalogue(first);

    for (auto filename : files) {
        FITSFile source(filename);
        updateImagelist(source);
        updateImages(source);
        currentImage += source.nimages();
    }
}

FitsUpdater::~FitsUpdater() {
    if (outfile) {
        delete outfile;
    }
}
