# Testing the tool

The test cases provided are functional; different example inputs are provided with references for what the outputs should be. Tests are ran using `pytest`:

```bash
pytest st-test.py -v
```

## Test cases
Test cases for the ac-tool, that uses fpp-to-json to be able to parse fpp files. This allows for the generation of other fpp files that define subtopology instances. The test cases cover a variety of potential issues that people could run into.

ex1:

    Tests a simple case where a single subtopology is instantiated

    Assert TRUE
    
ex2:

    Tests a case where a subtopology is instantiated multiple times

    Assert TRUE
    
ex3:

    Test a case with a mix of local and global component instances

    Assert TRUE
    
ex4:

    Test a case where a local component is tried to be replaced. 

    Assert FALSE
    
ex5:

    Test a syntax error

    Assert FALSE
    
ex6:

    Test a case where the locs file is invalid
    
    Assert FALSE