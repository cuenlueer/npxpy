# Code

## Minor

- Objects still can get arbitrary attributes assigned if accessed directly.
Consider mitigating this by refactoring such that Node only serves as the core functional basis and the attribute
assignments all go to the subnodes.
- Define setters (?) with errorchecking instead of checking only at init. Makes assigning values less prone to error
caused by faulty user input. Hotfix: __slots__ for each subclass!
- User convenience: Think about enabling type versatility with respect to iterables
(i.e., turn every input iterable to list) 

## Major

- A more "centralized" approach for data validation might be of interest. Especially when project.nano(). (databank?)

# Documentation

- Think about implementing more interactive elements (Jupyter Notebooks?)