# Overview

## About Plain programming language

Plain is a novel programming language that helps abstracting away complexity of using large language models for code generation.

Plain specification is rendered to software code that can be executed. You can therefore think of Plain as *executable specification*.

## Syntax

Plain language is structured English based on markdown syntax.

Here's an example of a "hello,world" program in Plain.

```plain
***Non-Functional Requirements:***

- Implementation should be in Python.

***Functional Requirements:***

- Display "hello, world"
```

# Source structure

## Source organization

Plain source can be organized in sections and subsection using markdown headers.

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

Every plain source file requires at least one functional requirement and an associated non-functional requirement.

Functional requirements must reside in leaf sections while other specifications can be placed also in non-leaf sections. Specifications in non-leaf sections apply not just to the section itself but to all of its subsections.

## Definitions

The `***Definitions:***` specification is a list of definitions of new terms.

Here's an example of a simple definiton.

```plain
- The App implements a task manager application.
```

The definitions should follow **The Noun convention**. That is, the introduced terms should start with the word **The** (capitalized) followed by a capitalized word (e.g. **The App**).

Definitons are the mechanism for definining data structures in Plain. Here's an example of a such a definition.

```plain
- The Task describes an activity that needs to be done by The User. The Task has the following attributes
  - Name - a short description of The Task. This is a required attribute. The name must be at least 3 characters long.
  - Notes - additional details about The Task
  - Due Date - optional date by which The User is supposed to complete The Task.
```

The definition of a term is provided in natural language. There are no restrictions on the form of the description. When referring to other terms **The Noun convention** should be followed.

## Non-Functional Requirements

The `***Non-Functional Requirements:***` specification is a list of instructions that steer software code implementation and provide details of execution environment.

Here's an example of a simple instruction specifying only that the Plain specification should be rendered to Python software code.

```plain
- Implementation should be in Python.
```

The instructions should be provided in natural language. There are no restrictions on the form or the complexity of the instruction except that they need to be given as a markdown list. When referring to other terms **The Noun convention** should be followed.

Here's an example of more complex instructions.

```plain
- Implementation of The Program should be in Python (The Implementation).

- The Implementation should include unit tests using Unittest framework (The Unittests).

- The main executable file of The Program should be called hello_world.py
```

## Functional Requirements

The `***Functional Requirements:***` specification provides a description of functionality that should be rendered to software code. The descriptions should be provided in natural language as a markdown list. When referring to other terms **The Noun convention** should be followed.

Here's an example of a simple description of the functionality of the "hello, world" application.

```plain
- Display "hello, world"
```

Each functional requirement must be limited in complexity. For example, for the functional requirement

```plain
- Implement a task manager application.
```

the renderer of Plain source to software code should respond with

```
Functional requirement too complex!
```

In such case you need to break down the functioanlity into smaller, less-complex functional requirements.

Here's an example how to do such a break down in the case of a task manager application.

```plain
- Implement the entry point for The App.

- Show The Task List.

- The User should be able to add The Task. Only valid The Task items can be added.

- The User should be able to delete The Task.

- The User should be able to edit The Task.

- The User should be able to mark The Task as completed.
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
    
  - The App shouldn't show logging output in the console output (neither in stdout nor stderr).
```

Acceptance tests extend **conformance tests**. The acceptance tests are implemented according to the ***Test Requirements:*** specification (see next section).

## Test Requirements

The `***Test Requirements:***` specification is a list of instructions that steer implementation of conformance tests and provide details of testing environment.

**Conformance tests** is the generated code used to verify that the functional requirement is implemented according to the specification.

Here's an example specification of test requirements.

```plain
- The Conformance Tests of The Program should be implemented in Python using Unittest framework. 
```

# Extended Syntax

## Comments

Lines starting with `>` are ignored when rendering software code.

```plain
> This is an example of a comment in Plain
```

## Linked Resources

If you include a link using the markdown syntax, the linked resource will be passed along with the Plain specification to the renderer.

Here's an example of a linked resource (see Task manager example application for the full specification).

```plain
- Show The Task List. The details of the user interface are provided in the file [task_list_ui_specification.yaml](task_list_ui_specification.yaml).
```

Please note that only links to files in the same folder (and its subfolders) as the Plain specification are supported. Links to external resources are not supported.

## Liquid templates

Plain supports Liquid templates. Liquid is an open-source template language created by Shopify (https://shopify.github.io/liquid/).

For a sample use of Liquid templates see [example-saas-connectors](https://github.com/Codeplain-ai/example-saas-connectors) repository.
