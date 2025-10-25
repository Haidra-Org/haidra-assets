# Haidra Python Style Guide

## Too long; didn't read

If this is your first time contributing, reference this document as you work rather than memorizing it. Many guidelines are enforced by linting or testing tools, and other rules can be followed by matching existing codebase patterns.

In brief:

- Descriptive, unambiguous naming is required; avoid abbreviations and acronyms unless widely understood.
- Never silently handle exceptions; always log or re-raise, and avoid blanket or bare excepts.
- All public APIs must have Google-style docstrings.
- Readability first: Prefer guard clauses, clear control flow, meaningfully named boolean expressions and avoid deeply nested structures.
- Type hints are mandatory for all public functions, methods, class attributes, and module-level variables.
- Code should be written for static analysis:
    - Avoid magic strings/numbers and direct dictionary access by key literals.
    - Prefer classes over dictionaries/tuples for data structures.
    - Use `Enum`/`StrEnum` for fixed sets of values.

These principles are opinionated and exist for consistency and maintainability. They don't claim to be the "best" way. Change proposals are welcome if something seems overly restrictive, missing, or could be improved.

## General Principles

- [PEP 20](https://peps.python.org/pep-0020/) should guide design and implementation, but not followed blindly.
- **All** function arguments and return values, class attributes and fields, and module-level variables must be type hinted.
    - See the [mypy type hint cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) for a primer.
    - Local variables only need type hints if mypy reports errors, but consider it good practice.
    - Use Python 3.10+ union types (`int | str`) instead of `typing.Union[int, str]` and use `| None` for optional types.
    - For most version of python, `typing_extensions` is a requirement to enable many used typing related features.
    - For self annotation and related functionality, begin the module with `from __future__ import annotations`.

## Naming Conventions

### Module and Package Naming

- Use lower snake_case with underscores between significant words or abbreviations.
    - Example: `ai_horde_api`, `generic_api`, `generation_parameters`
- Never use python builtin library names or popular third-party library names.
    - Banned examples: `logging`, `json`, `requests`

### Variable, Function, Method and Class Naming

- snake_case for variables, fields, functions, and methods with underscores between significant words or abbreviations.
- CamelCase for classes.
- ALL_CAPS_WITH_UNDERSCORES for constants.
- Prefix private variables and methods with a single underscore (`_private_variable`).
- **Do not reuse variable names** in overlapping scopes (e.g., outer function and inner function, loop variable and surrounding function).
    - For example:

    ```python
        # Bad
        def process_many_items(some_items: list[Item], special_items: list[SpecialItem]) -> None:

            for item in some_items:
                process_item(item)

            
            for item in special_items:  
                # item type is different here, causing confusion, breaks static analysis
                process_item(item)

        # Good
        def process_many_items(some_items: list[Item], special_items: list[SpecialItem]) -> None:

            for some_item in some_items:
                process_item(some_item)

            for special_item in special_items:
                process_item(special_item)

    ```

- **Names must be descriptive**. While ambiguity cannot always be avoided, strive for clarity.
    - Avoid vague names like `data`, `info`, `item`, `value`, `name` when a more specific name is possible.  
        - Context is important. Small functions or loops do not always need extremely descriptive names.
    - One/two/three letter variable names only allowed for:
        - Very small scope (e.g., `i` for a loop)
        - Mathematical context where variables have no significant meaning or are known by convention
        - Preserving external module/library naming for consistency
    - Avoid abbreviations unless **widely** understood (`url`, `api`, `id`) **and** they significantly improve readability.
        - "Widely" means most developers understand without lookup, not "common in some codebase" or "common in a narrow field."
        - Acceptable: `id`, `db`, `param`, `anon`, `obj`
        - Avoid: `img`, `num`, `cnt`, `val` (not considerably shorter, hurts readability)
        - Note: Python builtins methods such as `id` should *not* be used as the entire name of a variable.
            - For example, avoid:

            ```python
                # Bad
                id = get_user_id()

                # Good
                user_id = get_user_id()
            ```

            - For cases of remote API compatibility where `id` is required, prefer `id_` or `identifier` and alias appropriately. With pydantic models, use field aliases.
    - Acronyms should be widely understood and significantly improve readability.
        - Acceptable: `HTTP`, `URL`, `API`, `JSON`, `XML`, `HTML`
        - Avoid domain-specific or codebase-specific acronyms:

            ```python
                # Bad
                hr = HordeRequest(...)

                # Good
                horde_request = HordeRequest(...)
            ```

## Error Handling

- Never silently handle exceptions. Always log and/or re-raise.
- Use exceptions for exceptional cases, not control flow.
- Bare `except:` statements forbidden (they catch system-exiting exceptions like `KeyboardInterrupt`).
- Avoid blanket catches (`except Exception as e:`) unless necessary.
    - If used, consider making excepts opt-in with default `raise e`.
    - Exception: resource cleanup or finalization tasks (e.g., `__exit__` methods).
    - Otherwise, catch only specific expected exceptions you can handle appropriately.

## Documentation and Docstrings

- All public modules, classes, methods, variables and fields must have [Google-style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) docstrings.
    - First line should be imperative mood and briefly summarize purpose (avoid restating method name unless narrow/trivial).
    - `@override` methods inherit parent docstrings unless behavior significantly differs (consider refactoring if so).

- Module docstrings:
    - Summarize the module's purpose.
    - List and briefly describe critical public classes, functions, and variables.
    - Provide any additional context, including caveats about import order or side effects.
- Class docstrings:
    - Summarize the class's purpose and behavior.
    - Data-class or pydantic models' docstring should begin with "Represents..."
    - Add any additional sections as appropriate (e.g., `Examples:`).
        - See also the [mkdocs enabled projects](#mkdocs-enabled-projects) section below.
- Function/Method docstrings:
    - Methods that:
            - Return a value, should start with "Return..."
                - Unless the method is a factory/creator method or has a special semantic meaning
                - For example:
                    - A method decorator with `@contextmanager` should start with "Context manager {that/for/etc}..."
                    - A method that modifies an object in place should start with "Mutate..."
                    - Async methods should not document the Coroutine object itself, but the eventual returned value.
                        - It should, however, highlight that it is async if not obvious from the name.
            - Create a returned value should start with "Create a {type/description}..."
            - Primarily convert, parse, or validate data should start with "Convert...", "Parse...", or "Validate..."
        - Other conventions beyond this are flexible, but should remain consistent within a codebase.
    - Use the `Args:` section to document each parameter, if any.
        - Args should be listed in the same order as the function signature.
    - Use the `Returns:` section to document the return value, if any.
    - Use the `Raises:` section to document any exceptions that may be raised.
        - Document likely exceptions (`FileNotFoundError`, `IOError` for file operations; `ConnectionError`, `TimeoutError` for network calls).
        - Note: This does not mean you need to document every possible exception that could be raised, only those that are part of the method's contract, are likely to be encountered by users of the method, or foreseeable by the method's implementation.
  
### mkdocs enabled projects

- Class docstrings should use the following additional headers as appropriate (these are not required for every class, only when relevant):
    - `Thread Safety`: Document whether the class is thread-safe, and any synchronization mechanisms used.
    - `Subclass Integration`: Especially for abstract base classes, document how subclasses should implement/extend behavior.
    - `Examples`: Provide usage examples, especially for complex classes or those with non-obvious behavior.
    - Any additional headings which are appropriate for the specific class. For example, a class representing a network connection might include a `Connection Management` section.
- Function docstrings should use the following additional header if appropriate (these are not required for every function, only when relevant):
    - `Side Effects`: Document any side effects, such as modifying global state, files, or network resources.
    - `Concurrency`: Document whether the function is thread-safe, and any synchronization mechanisms used.
    - `Performance`: Note any performance considerations, such as time complexity or resource usage.
    - `Examples`: Provide usage examples, especially for complex functions or those with non-obvious behavior.
    - Any additional headings which are appropriate for the specific function. For example, a function that performs network I/O might include a `Network Behavior` section.
- Use mkdocstring links where appropriate to reference other documented classes, methods, or functions within the same codebase.
    - You must use the fully qualified name (including module path) for all cross-references.
        - For example:
            - ```[`Object 1`][full.path.object1] # With a custom title```
            - ```[`Object 2`][full.path.object2] # With the identifier as title```
    - Only make cross-references to external libraries if they have been configured for this in the mkdocstring configuration.

    - See the [mkdocstring documentation](https://mkdocstrings.github.io/usage/#cross-references/) for details on syntax and usage.

## Function and Method Signatures

- Prefer keyword-only arguments when multiple arguments have the same type or are adjacent, improving readability, preventing order mistakes and allowing future signature changes without breaking callers:

    ```python
        # Avoid
        def create_user(name: str, age: int, username: str, email: str):

        # Prefer
        def create_user(*, name: str, age: int, username: str, email: str):
    ```

## Object-Oriented Design

- Embrace Python's dynamic nature for public interfaces when doing so follows common python idioms and improves usability.
    - Strict `isinstance(...)` checks are discouraged unless necessary for network IO/user input safety.
- Use inheritance for "is a" relationships, composition for "has a" relationships.
- Favor interfaces and abstract base classes for public APIs (allows implementation flexibility).
- Use `@override` when overriding methods.

## Method Overloading and Return Types

- Avoid surprisingly overloaded methods with ambiguous behavior. Create separate methods instead:

    ```python
        # Bad
        def process_item(item: Item) -> None:
            if hasattr(item, '__iter__'):
                # handles both single items and lists unpredictably

        # Good
        def process_items(items: list[Item]) -> None:
        def process_single_item(item: Item) -> None:
            process_items([item])
    ```

- Return predictable types:
    - Avoid returning `None` as catch-all failure indication. Raise exceptions or return specific failure values.
    - `None` should only indicate its usual meaning (missing/unset), not overloaded failure types.
    - Accept abstract types (`Iterable`, `Mapping`) for parameters, return concrete types unless specifically designed otherwise:

        ```python
            # Return: concrete so consumers know what to expect
            def get_items(self) -> list[Item]:  # Not Iterable[Item]

            # Parameter and return concrete type: specific expected type
            def parse_item(item: Item) -> ParsedItem:

            # Parameter and return type: abstract for flexibility, as callers can pass various types
            def mutate_items(items: Iterable[Item]) -> Iterable[Item]:
        ```

        > Note: This is not a hard and fast rule; use judgment based on context and the likelihood that the internal implementation or consumer usage may change.

    - Use `Any` judiciously; only when more specific types aren't possible and consumers don't need to know the type.
    - Methods should not return different types based on parameters:

        ```python
            # Bad
            def get_items(self, as_list: bool = True) -> list[Item] | set[Item]:

            # Good
            def get_items(self) -> list[Item]:
            def get_unique_items(self) -> set[Item]:
        ```

    - Always return containers consistently, even for single items:

        ```python
            # Bad
            def get_items(self) -> list[Item] | Item:

            # Good
            def get_items(self) -> list[Item]:
        ```

## Control Flow and Readability

- Prefer guard clauses over deeply nested if statements:

    ```python
    # Avoid
    def process_item(item: Item):
        if item is not None:
            if item.is_valid():
                # process item

    # Prefer
    def process_item(item: Item):
        if item is None or not item.is_valid():
            return
        # process item
    ```

- Use meaningfully named composite `bool` conditionals:

    ```python
    # Bad - complex nested conditions that are hard to understand
    def do_request(request: Request, worker: Worker) -> bool:
        if ((request.model in worker.models and request.size <= worker.max_size) or
            request.is_priority) and worker.available and request.safe:
            # process request
            return True
        # skip request
        return False

    # Better - break down complex logic into named intermediate variables
    def do_request(request: Request, worker: Worker) -> bool:
        if can_process_request(request, worker):
            # process request
            return True
        # skip request
        return False

    def can_process_request(request: Request, worker: Worker) -> bool:
        model_compatible = request.model in worker.models and request.size <= worker.max_size
        can_accept = model_compatible or request.is_priority
        
        return can_accept and worker.available and request.safe

    # Even Better - extract validation logic into focused, reusable methods
    def do_request(request: Request, worker: Worker) -> bool:
        if can_process_request(request, worker):
            # process request
            return True
        # skip request
        return False

    def can_process_request(request: Request, worker: Worker) -> bool:
        return _is_request_compatible(request, worker) and _worker_is_ready(worker, request)

    def _is_request_compatible(request: Request, worker: Worker) -> bool:
        return (request.model in worker.models and request.size <= worker.max_size) or request.is_priority

    def _worker_is_ready(worker: Worker, request: Request) -> bool:
        return worker.available and request.safe
    ```

## Data Structures, Models, and Constants

- Prefer classes over dictionaries or anonymous data structures.
    - Use [pydantic](https://docs.pydantic.dev/) `BaseModel` for data structures when validation/conversion is needed.
    - Use simple classes when robust validation isn't needed or performance is a concern.
- Use properties for read-only access; avoid exposing mutable members (return copies instead).
- Magic strings/numbers are evil. Use `StrEnum`/`Enum` for specific valid values, constants for isolated values. Members should be capitalized.
    - Use `StrEnum` when string representation is needed (e.g., JSON serialization, external APIs):
  
   ```python
         from enum import auto()
         from strenum import StrEnum
    
         class Color(StrEnum):
              RED = auto()
              GREEN = auto()
              BLUE = auto()
    ```

- Group related constants into classes:

    ```python
        class APIConfig:
            MAX_RETRIES = 5
            TIMEOUT = 30
            JITTER = 0.1
    ```

- If your settings are user-configurable, use `pydantic-settings`'s `BaseSettings` for environment variable support:
  
    ```python
        from pydantic import BaseModel
        from pydantic_settings import BaseSettings

        class MyAppSubModuleSettings(BaseModel):
            feature_enabled: bool = True
            max_connections: int = 10

        class AppSettings(BaseSettings):
            api_key: str
            debug_mode: bool = False
            submodule: MyAppSubModuleSettings = MyAppSubModuleSettings()

            class Config:
                env_file = ".env"
    ```

## Imports and Module Export

- Star imports (`import * from <module>`) are forbidden.
- Significant namespaces must explicitly export public members via `__all__`.

## Third-Party Library Specific Guidelines

### Pydantic BaseModel Usage

- Use `BaseModel` derived classes DataClass-like without side effects or state mutation.
    - Methods should be limited to validation/conversion with narrow scope - avoid business logic.
        - Functions extending beyond `isinstance` or value checking should likely be moved elsewhere.
        - In the case you find yourself needing more complex behavior, consider using a regular class which contains a `BaseModel` instance as a member. For smaller scopes, consider utility functions that accept the model as an argument.
    - Never coerce non-`None` values to `None` for optional fields.
    - API responses and client/server/worker data should be frozen using `model_config`.
        - Use any existing default configuration factories in your codebase. In many Haidra-Org modules, this is in the `__init__.py` file of the top-level package.
