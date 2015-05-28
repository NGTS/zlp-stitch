#include <iostream>
#include <tclap/CmdLine.h>
#include <fitsio.h>
#include <stdexcept>
#include <map>
#include <set>
#include <algorithm>

#include "fits_file.h"
#include "fits_updater.h"

using namespace std;

string toUpper(const string &s) {
    string tmp = s;
    for_each(tmp.begin(), tmp.end(),
             [](char &c) { c = toupper((unsigned char)c); });
    return tmp;
}

ImageDimensions get_image_dimensions(const vector<string> &files) {
    ImageDimensions out = {0, 0};

    for (auto filename : files) {
        FITSFile source(filename);
        source.toHDU("FLUX");
        ImageDimensions dim = source.imageDimensions();
        if ((out.napertures == 0) && (out.nimages == 0)) {
            out.napertures = dim.napertures;
            out.nimages = dim.nimages;
        } else {
            if (dim.napertures != out.napertures) {
                throw runtime_error("Image dimensions do not match");
            }

            out.nimages += dim.nimages;
        }
    }

    return out;
}

map<string, ColumnDefinition> get_columns(const vector<string> &files,
                                          const string &hduname) {
    map<string, ColumnDefinition> out;
    for (auto filename : files) {
        FITSFile source(filename);
        source.toHDU(toUpper(hduname));

        auto column_description = source.column_description();

        for (auto column : column_description) {
            if (out.find(column.first) == out.end()) {
                out.insert(column);
            } else {
                int new_type = column.second.type;
                int old_type = out[column.first].type;
                if (new_type > old_type) {
                    out[column.first] = column.second;
                }
            }
        }
    }
    return out;
}

vector<string> sort_files_by_mjd_range(const vector<string> &files) {
    auto tmp = files;
    sort(tmp.begin(), tmp.end(), [](const string &a, const string &b) -> bool {
        double a_min = FITSFile(a).mjd_range().min;
        double b_min = FITSFile(b).mjd_range().min;
        return a_min < b_min;
    });
    return files;
}

set<string> get_image_names(const vector<string> &files) {
    set<string> out;
    for (auto filename : files) {
        int nhdu = -1;
        FITSFile source(filename);
        fits_get_num_hdus(source.fptr, &nhdu, &source.status);
        source.check();

        for (int i = 2; i < nhdu; i++) {
            char buf[FLEN_VALUE];
            source.toHDU(i);
            int hdutype = -1;
            fits_get_hdu_type(source.fptr, &hdutype, &source.status);
            source.check();
            if (hdutype == IMAGE_HDU) {
                fits_read_key(source.fptr, TSTRING, "EXTNAME", buf, NULL,
                              &source.status);
                source.check();
                out.insert(buf);
            }
        }
    }
    return out;
}

void stitch(const vector<string> &files, const string &output) {
    auto sorted_files = sort_files_by_mjd_range(files);
    auto image_dimensions = get_image_dimensions(sorted_files);
    cout << "Image dimensions => nimages: " << image_dimensions.nimages
         << ", napertures: " << image_dimensions.napertures << endl;
    auto imagelist_columns = get_columns(sorted_files, "IMAGELIST");
    auto catalogue_columns = get_columns(sorted_files, "CATALOGUE");
    set<string> image_names = get_image_names(sorted_files);

    FitsUpdater updater(image_dimensions, imagelist_columns, catalogue_columns,
                        image_names);
    updater.render(files, output);
    cout << "Complete" << endl;
}

int main(int argc, char *argv[]) {
    try {
        TCLAP::CmdLine cmd("zlp-stitch", ' ', "0.0.1");
        TCLAP::ValueArg<string> output_arg("o", "output", "output file", true,
                                           "", "FILE", cmd);
        TCLAP::UnlabeledMultiArg<string> filename_arg(
            "filename", "file to analyse", true, "FILE", cmd);
        cmd.parse(argc, argv);

        stitch(filename_arg.getValue(), output_arg.getValue());

        return 0;
    } catch (TCLAP::ArgException &e) {
        cerr << "error: " << e.error() << " for arg " << e.argId() << endl;
    }
}
