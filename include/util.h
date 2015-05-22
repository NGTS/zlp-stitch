#ifndef UTIL_H

#define UTIL_H

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

#endif /* end of include guard: UTIL_H */
