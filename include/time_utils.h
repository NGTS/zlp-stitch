#ifndef TIME_UTILS_H

#define TIME_UTILS_H

#include <string>

const std::string current_time();

#define log std::cout << "[" << current_time() << "] "

#endif /* end of include guard: TIME_UTILS_H */
