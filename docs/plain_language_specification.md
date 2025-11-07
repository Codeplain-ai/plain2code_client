# Overview

## About ***plain

***plain is a novel specification language that helps abstracting away complexity of using large language models for code generation.

***plain specification is rendered to software code that can be executed. You can therefore think of ***plain as *executable specification*.

## Syntax

***plain language is structured English based on markdown syntax.

Here's an example of a "hello,world" app in ***plain.

```plain
***Non-Functional Requirements:***

- Implementation should be in Python.

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

- Simple non-functional requirement

## Section 2.1

***Functional Requirements:***

- Simple functional requirement
```

### Specifications

There are four types of specifications:

- `***Definitions:***`
- `***Non-Functional Requirements:***`
- `***Functional Requirements:***`
- `***Test Requirements:***`

Every ***plain source file requires at least one functional requirement and an associated non-functional requirement.

Functional requirements must reside in leaf sections while other specifications can be placed also in non-leaf sections. Specifications in non-leaf sections apply not just to the section itself but to all of its subsections.

## Definitions

The `***Definitions:***` specification is a list of definitions of new terms.

Here's an example of a simple definiton.

```plain
- :App: implements a task manager application.
```

The definitions should follow **:ConceptName:** convention how to name concepts defined in the definitions sections.

Definitons are the mechanism for definining data structures in ***plain. Here's an example of a such a definition.

```plain
- :Task: describes an activity that needs to be done by :User:. :Task: has the following attributes
  - Name - a short description of :Task:. This is a required attribute. The name must be at least 3 characters long.
  - Notes - additional details about :Task:
  - Due Date - optional date by which :User: is supposed to complete :Task:.
```

The definition of a term is provided in natural language. There are no restrictions on the form of the description. When referring to other terms **:ConceptName:** convention should be followed.

## Non-Functional Requirements

The `***Non-Functional Requirements:***` specification is a list of instructions that steer software code implementation and provide details of execution environment.

Here's an example of a simple instruction specifying only that the ***plain specification should be rendered to Python software code.

```plain
- Implementation should be in Python.
```

The instructions should be provided in natural language. There are no restrictions on the form or the complexity of the instruction except that they need to be given as a markdown list. When referring to other terms **:ConceptName:** convention should be followed.

Here's an example of more complex instructions.

```plain
- :Implementation: should be in Python.

- :Implementation: should include :Unittests: using Unittest framework.

- The main executable file of :App: should be called hello_world.py
```

## Functional Requirements

The `***Functional Requirements:***` specification provides a description of functionality that should be rendered to software code. The descriptions should be provided in natural language as a markdown list. When referring to other terms **:ConceptName:** convention should be followed.

Here's an example of a simple description of the functionality of the "hello, world" application.

```plain
- Display "hello, world"
```

Each functional requirement must be limited in complexity. For example, for the functional requirement

```plain
- Implement a task manager application.
```

the renderer of ***plain source to software code should respond with

```
Functional requirement too complex!
```

In such case you need to break down the functioanlity into smaller, less-complex functional requirements.

Here's an example how to do such a break down in the case of a task manager application.

```plain
- Implement the entry point for :App:.

- Show :TaskList:.

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

***plain supports template inclusion using the `{% include %}` syntax, which allows you to use predefined templates in your specifications.

```plain
{% include "python-console-app-template.plain", main_executable_file_name: "my_app.py" %}
```
Predefined templates are available for Go console apps, Python console apps, and TypeScript React apps in the [standard template library](../standard_template_library/). You can also create your own custom templates.

The template system enables code reuse and standardization across ***plain projects.

## Linked Resources

If you include a link using the markdown syntax, the linked resource will be passed along with the ***plain specification to the renderer.

Here's an example of a linked resource (see Task manager example application for the full specification).

```plain
- Show :TaskList:. The details of the user interface are provided in the file [task_list_ui_specification.yaml](task_list_ui_specification.yaml).
```

**Important Notes:**
- Only links to files in the same folder (and its subfolders) as the ***plain specification are supported. Links to external resources are not supported.
- File paths are resolved relative to the location of the ***plain specification file.
- All types are supported, except binary files.

### Hierarchical Resource Visibility

Due to the hierarchical structure of the ***plain specification, file attachments follow a scoping rule: **a functional requirement can only access linked resources that are defined in its own section or in any parent section**.

Here's an example demonstrating this hierarchical nature:

```plain
# Section 1

***Non-Functional Requirements:***

- Simple non-functional requirement with [file_attachment_1.yaml](file_attachment_1.yaml)

# Section 2

***Non-Functional Requirements:***

- Simple non-functional requirement with [file_attachment_2.yaml](file_attachment_2.yaml)

## Section 2.1

***Functional Requirements:***

- Simple functional requirement with [file_attachment_2_1.yaml](file_attachment_2_1.yaml)
```

**Resource visibility for Section 2.1:**
- ✅ `file_attachment_2_1.yaml` - same section
- ✅ `file_attachment_2.yaml` - parent section (Section 2)
- ❌ `file_attachment_1.yaml` - sibling section (Section 1), not accessible

This hierarchical scoping ensures that resources are properly encapsulated and prevents accidental access to unrelated files.

This design allows you to optimize context size by attaching only the necessary resources to the functional requirements that need them, improving the performance of the rendering process.

## Liquid templates

***plain supports Liquid templates. Liquid is an open-source template language created by Shopify (https://shopify.github.io/liquid/).

For a sample use of Liquid templates see [example-saas-connectors](https://github.com/Codeplain-ai/example-saas-connectors) repository.
