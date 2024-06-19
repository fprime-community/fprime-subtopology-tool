include(autocoder/helpers)

set(PYTHON_TOOL "<< FILL THIS IN >>")

autocoder_setup_for_individual_sources()

function(subtopology_is_supported AC_INPUT_FILE)
    autocoder_support_by_suffix(".fpp" "${AC_INPUT_FILE}" TRUE)
endfunction(subtopology_is_supported)

function(subtopology_setup_autocode AC_INPUT_FILE)
    get_filename_component(BASENAME "${AC_INPUT_FILE}" NAME)
    message(STATUS "Checking for subtopology instances in ${BASENAME}")

    set(OUTPUT_FILE "${CMAKE_CURRENT_BINARY_DIR}/${FPRIME_CURRENT_MODULE}.subtopologies.fpp")
    set(LOCAL_CACHE "${CMAKE_CURRENT_BINARY_DIR}/fpp-cache")

    set(GENERATED_FILES "${CMAKE_CURRENT_BINARY_DIR}/${FPRIME_CURRENT_MODULE}.subtopologies.fpp" "${CMAKE_CURRENT_BINARY_DIR}/st-locs.fpp")

    if (CMAKE_DEBUG_OUTPUT)
        message(STATUS "[Subtopology Ac] CLI: ${PYTHON} ${PYTHON_TOOL} --locs ${CMAKE_BINARY_DIR}/locs.fpp --file ${AC_INPUT_FILE} --p ${OUTPUT_FILE} --c ${LOCAL_CACHE}")
    endif()

    execute_process(
        COMMAND ${PYTHON} ${PYTHON_TOOL} --locs ${CMAKE_BINARY_DIR}/locs.fpp --file ${AC_INPUT_FILE} --p ${GENERATED_FILES} --c ${LOCAL_CACHE}
        RESULT_VARIABLE RETURN_CODE
    )
    
    if (RETURN_CODE EQUAL 0)
        set(AUTOCODER_GENERATED "${GENERATED_FILES}" PARENT_SCOPE)
    else()
        set(AUTOCODER_GENERATED "" PARENT_SCOPE)
    endif()
endfunction(subtopology_setup_autocode)