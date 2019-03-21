#ifndef UTIL_H
#define UTIL_H

#include <string>
#include <vector>

#include "spdlog/spdlog.h"
#include "spdlog/sinks/stdout_color_sinks.h"

extern std::shared_ptr<spdlog::logger> logger;

#define BITGEN_SPDLOG_STR_H(x) #x
#define BITGEN_SPDLOG_STR_HELPER(x) BITGEN_SPDLOG_STR_H(x)

#define TRACE(...) do { \
    logger->trace("[" __FILE__ ":" BITGEN_SPDLOG_STR_HELPER(__LINE__) "] " __VA_ARGS__); \
} while (false); \

#define DEBUG(...) do { \
    logger->debug("[" __FILE__ ":" BITGEN_SPDLOG_STR_HELPER(__LINE__) "] " __VA_ARGS__); \
} while (false); \

#define INFO(...) do { \
    logger->info("[" __FILE__ ":" BITGEN_SPDLOG_STR_HELPER(__LINE__) "] " __VA_ARGS__); \
} while (false); \

#define WARN(...) do { \
    logger->warn("[" __FILE__ ":" BITGEN_SPDLOG_STR_HELPER(__LINE__) "] " __VA_ARGS__); \
} while (false); \

#define ERROR(...) do { \
    logger->error("[" __FILE__ ":" BITGEN_SPDLOG_STR_HELPER(__LINE__) "] " __VA_ARGS__); \
} while (false); \

#define CRITICAL(...) do { \
    logger->critical("[" __FILE__ ":" BITGEN_SPDLOG_STR_HELPER(__LINE__) "] " __VA_ARGS__); \
} while (false); \

std::string bitstream_to_string(const std::vector<bool> & bitstream);

std::vector<std::string> split(const std::string & str, const std::string & delim);

#endif /* UTIL_H */
