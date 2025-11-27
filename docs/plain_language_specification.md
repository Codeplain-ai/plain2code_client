# Overview

## About ***plain programming language

***plain is a novel programming language that helps abstracting away complexity of using large language models for code generation.

***plain specification is rendered to software code that can be executed. You can therefore think of ***plain as *executable specification*.

## Syntax

***plain language is structured English based on markdown syntax.

Here's an example of a "hello, world" program in ***plain.

```plain
***Non-Functional Requirements:***

- :Implementation: should be in Python.

***Functional Requirements:***

- Display "hello, world"
```

# Source structure

## Source organization

***plain source can be organized in sections and subsection using markdown headers.

```plain
# Section 1

# Section 2

***Non-Functional Requirements:***

- First simple non-functional requirement

***Functional Requirements:***

- First simple functional requirement

## Section 2.1

***Non-Functional Requirements:***

- Second simple non-functional requirement

***Functional Requirements:***

- Second simple functional requirement
```

This enables hierarchical organization of the specification. 

In example above:

- While rendering the "First simple functional requirement", the renderer will not have access to the "Second simple non-functional requirement".
- While rendering the "Second simple functional requirement", the renderer will not have access to the "First simple non-functional requirement".

### Specifications

There are four types of specifications:

- `***Definitions:***`
- `***Non-Functional Requirements:***`
- `***Functional Requirements:***`
- `***Test Requirements:***`

Every plain source file requires at least one functional requirement and an associated non-functional requirement.

Functional requirements must reside in leaf sections while other specifications can be placed also in non-leaf sections. Specifications in non-leaf sections apply not just to the section itself but to all of its subsections.

## Definitions

The `***Definitions:***` specification is a list of definitions of new concepts.

Here's an example of a simple definiton.

```plain
- :App: implements a task manager application.
```

In this case, the concept name is `:App:`. Concepts are important for refering to definitions in the rest of the specification.

While providing definitions, you should adhere to the following 4 rules:

- Every definition must start with the name of the concept you are defining.
- Each concept name must be enclosed in colons (`:`) at both the beginning and end.
  - Valid characters for concept name include: Plus sign (`+`), Minus sign (`-`), Dot sign (`.`), Digits (`0`-`9`), Uppercase letters (`A`-`Z`), Underscore (`_`), Lowercase letters (`a`-`z`)
  - Examples: `:App:`, `:Tasks:`, `:ListOfUsers:`, `:CLI:`. 
- Concept names must be globally unique (meaning, you cannot provide two definitions with the same concept name).
- When referencing concepts in ***Test Requirements:***, ***Functional Requirements:***, ***Non-Functional Requirements:*** and ***Acceptance Tests:***, the concept name must exist in the ***Definitions:*** section.

Furthermore, there are special concepts that are already defined and are ready to use. They should not be redefined:

- `:ConformanceTests:`
- `:UnitTests:`
- `:AcceptanceTests:`
- `:Implementation:`

Definitions are the mechanism for definining data structures in ***plain. Here's an example of two definitions.

```plain
- :User: is a person who uses the application.

- :Task: describes an activity that needs to be done by :User:. :Task: has the following attributes:
  - Name - a short description of :Task:. This is a required attribute. The name must be at least 3 characters long.
  - Notes - additional details about :Task:
  - Due Date - optional date by which :User: is supposed to complete :Task:.
```

## Non-Functional Requirements

The `***Non-Functional Requirements:***` specification is a list of instructions that steer software code implementation and provide details of execution environment.

Here's an example of a simple instruction specifying only that the Plain specification should be rendered to Python software code.

```plain
- :Implementation: should be in Python.
```

The instructions should be provided in natural language. There are no restrictions on the form or the complexity of the instruction except that they need to be given as a markdown list.

Here's an example of more complex instructions.

```plain
- :Implementation: of :App: should be in Python.

- :Implementation: should include unit tests using Unittest framework.

- The main executable file of :App: should be called hello_world.py
```

## Functional Requirements

The `***Functional Requirements:***` specification provides a description of functionality that should be rendered to software code. The descriptions should be provided in natural language as a markdown list.

Here's an example of a simple description of the functionality of the "hello, world" application.

```plain
- Display "hello, world"
```

Each functional requirement must be limited in complexity. For example, for the functional requirement

```plain
- :App: should implement a task manager application.
```

the renderer of Plain source to software code should respond with

```
Functional requirement too complex!
```

In such case you need to break down the functioanlity into smaller, less-complex functional requirements.

Here's an example how to do such a break down in the case of a task manager application.

```plain
- Implement the entry point for :App:.

- Show :Task: List.

- :User: should be able to add :Task:. Only valid :Task: items can be added.

- :User: should be able to delete :Task:.

- :User: should be able to edit :Task:.

- :User: should be able to mark :Task: as completed.
```

Functional requirements are rendered incrementally one by one. Consequently earlier functional requirements cannot reference later functional requirements.

### Acceptance Tests

Acceptance tests can be used to further refine the functional requirement and especially to incorporate constraints on the implementation.

Acceptance tests are specified with a keyword `***Acceptance Tests:***` as a subsection within `***Functional Requirements:***` section. Each acceptance tests must be an item in a list.

Here's an example of a "Hello, World" application with one acceptance test.

```plain
***Functional Requirements:***

- Display "hello, world"

  ***Acceptance Tests:***
    
  - :App: shouldn't show logging output in the console output (neither in stdout nor stderr).
```

Acceptance tests extend **conformance tests**. The acceptance tests are implemented according to the ***Test Requirements:*** specification (see next section).

## Test Requirements

The `***Test Requirements:***` specification is a list of instructions that steer implementation of conformance tests and provide details of testing environment.

**Conformance tests** is the generated code used to verify that the functional requirement is implemented according to the specification.

Here's an example specification of test requirements.

```plain
- :ConformanceTests: of :App: should be implemented in Python using Unittest framework. 
```

# Extended Syntax

## Comments

Lines starting with `>` are ignored when rendering software code.

```plain
> This is an example of a comment in ***plain
```

## Template System

Plain supports template inclusion using the `{% include %}` syntax, which allows you to use predefined templates in your specifications.

```plain
{% include "python-console-app-template.plain", main_executable_file_name: "my_app.py" %}
```
Predefined templates are available for Go console apps, Python console apps, and TypeScript React apps in the [standard template library](../standard_template_library/). You can also create your own custom templates.

The template system enables code reuse and standardization across Plain projects.

## Linked Resources

If you include a link using the markdown syntax, the linked resource will be passed along with the Plain specification to the renderer.

Here's an example of a linked resource (see Task manager example application for the full specification).

```plain
- Show :Task: List. The details of the user interface are provided in the file [task_list_ui_specification.yaml](task_list_ui_specification.yaml).
```

**Important Notes:**
- Only links to files in the same folder (and its subfolders) as the Plain specification are supported. Links to external resources are not supported.
- File paths are resolved relative to the location of the Plain specification file.
- All types are supported, except binary files.

## Liquid templates

Plain supports Liquid templates. Liquid is an open-source template language created by Shopify (https://shopify.github.io/liquid/).

For a sample use of Liquid templates see [example-saas-connectors](https://github.com/Codeplain-ai/example-saas-connectors) repository.
