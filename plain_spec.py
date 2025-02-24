import copy


DEFINITIONS = 'Definitions:'
NON_FUNCTIONAL_REQUIREMENTS = 'Non-Functional Requirements:'
TEST_REQUIREMENTS = 'Test Requirements:'
FUNCTIONAL_REQUIREMENTS = 'Functional Requirements:'

ALLOWED_SPECIFICATION_HEADINGS = [DEFINITIONS, NON_FUNCTIONAL_REQUIREMENTS, TEST_REQUIREMENTS, FUNCTIONAL_REQUIREMENTS]


def collect_specification_linked_resources(specification, specification_heading, linked_resources_list):
    linked_resources = []
    if 'linked_resources' in specification:
        linked_resources.extend(specification['linked_resources'])

    for resource in linked_resources:
        resource_found = False
        for resource_map in linked_resources_list:
            if resource['text'] == resource_map['text']:
                if resource['target'] != resource_map['target']:
                    raise Exception(f"The file {resource['target']} is linked to multiple linked resources with the same text: {resource['text']}")
            elif resource['target'] == resource_map['target']:
                if resource['text'] != resource_map['text']:
                    raise Exception(f"The linked resource {resource['text']} is linked to multiple files: {resource_map['target']}")
            else:
                continue

            if resource_found:
                raise Exception("Duplicate linked resource found: " + resource['text'] + " (" + resource['target'] + ")")

            resource_found = True
            resource_map['sections'].append(specification_heading)

        if not resource_found:
            linked_resources_list.append({
                'text': resource['text'],
                'target': resource['target'],
                'sections': [specification_heading]
            })


def collect_linked_resources_in_section(section, linked_resources_list, frid=None):
    for specification_heading in [DEFINITIONS, NON_FUNCTIONAL_REQUIREMENTS, TEST_REQUIREMENTS]:
        if specification_heading in section:
            for requirement in section[specification_heading]:
                collect_specification_linked_resources(requirement, specification_heading, linked_resources_list)

    if FUNCTIONAL_REQUIREMENTS in section:
        functional_requirement_count = 0
        for requirement in section[FUNCTIONAL_REQUIREMENTS]:
            collect_specification_linked_resources(requirement, FUNCTIONAL_REQUIREMENTS, linked_resources_list)

            functional_requirement_count += 1
            if 'ID' in section:
                current_frid = section['ID'] + "." + str(functional_requirement_count)
            else:
                current_frid = str(functional_requirement_count)

            if current_frid == frid:
                return True

    if 'sections' in section:
        for subsection in section['sections']:
            if collect_linked_resources_in_section(subsection, linked_resources_list, frid):
                return True

    return False


def collect_linked_resources(plain_source_tree, linked_resources_list, frid=None):

    if not isinstance(plain_source_tree, dict):
        raise ValueError("[plain_source_tree must be a dictionary.")

    if frid is not None:
        functional_requirements = get_frids(plain_source_tree)
        if frid not in functional_requirements:
            raise ValueError(f"frid {frid} does not exist.")

    return collect_linked_resources_in_section(plain_source_tree, linked_resources_list, frid)


def get_frids(plain_source_tree):
    if FUNCTIONAL_REQUIREMENTS in plain_source_tree:
        for functional_requirement_id in range(1, len(plain_source_tree[FUNCTIONAL_REQUIREMENTS]) + 1):
            if 'ID' in plain_source_tree:
                yield plain_source_tree['ID'] + "." + str(functional_requirement_id)
            else:
                yield str(functional_requirement_id)

    if 'sections' in plain_source_tree:
        for section in plain_source_tree['sections']:
            yield from get_frids(section)


def get_first_frid(plain_source_tree):
    return next(get_frids(plain_source_tree), None)


def get_next_frid(plain_source_tree, frid):
    functional_requirements = get_frids(plain_source_tree)
    for temp_frid in functional_requirements:
        if temp_frid == frid:
            return next(functional_requirements, None)

    raise Exception(f"Functional requirement {frid} does not exist.")


def get_previous_frid(plain_source_tree, frid):
    previous_frid = None
    for temp_frid in get_frids(plain_source_tree):
        if temp_frid == frid:
            return previous_frid

        previous_frid = temp_frid

    raise Exception(f"Functional requirement {frid} does not exist.")


def get_specifications_from_plain_source_tree(frid, plain_source_tree, definitions, non_functional_requirements, test_requirements, functional_requirements, section_id=None):
    return_frid = None
    if FUNCTIONAL_REQUIREMENTS in plain_source_tree and len(plain_source_tree[FUNCTIONAL_REQUIREMENTS]) > 0:
        functional_requirement_count = 0
        for functional_requirement in plain_source_tree[FUNCTIONAL_REQUIREMENTS]:
            functional_requirement_count += 1
            if section_id is None:
                current_frid = str(functional_requirement_count)
            else:
                current_frid = section_id + "." + str(functional_requirement_count)

            functional_requirements.append(functional_requirement['markdown'])

            if current_frid == frid:
                return_frid = current_frid
                break

    if 'sections' in plain_source_tree:
        for section in plain_source_tree['sections']:
            sub_frid = get_specifications_from_plain_source_tree(frid, section, definitions, non_functional_requirements, test_requirements, functional_requirements, section['ID'])
            if sub_frid is not None:
                return_frid = sub_frid
                break

    if return_frid is not None:
        if DEFINITIONS in plain_source_tree and plain_source_tree[DEFINITIONS] is not None:
            definitions[0:0] = [specification['markdown'] for specification in plain_source_tree[DEFINITIONS]]
        if NON_FUNCTIONAL_REQUIREMENTS in plain_source_tree and plain_source_tree[NON_FUNCTIONAL_REQUIREMENTS] is not None:
            non_functional_requirements[0:0] = [specification['markdown'] for specification in plain_source_tree[NON_FUNCTIONAL_REQUIREMENTS]]
        if TEST_REQUIREMENTS in plain_source_tree and plain_source_tree[TEST_REQUIREMENTS] is not None:
            test_requirements[0:0] = [specification['markdown'] for specification in plain_source_tree[TEST_REQUIREMENTS]]

    return return_frid


def get_specifications_for_frid(plain_source_tree, frid):
    definitions = []
    non_functional_requirements = []
    test_requirements = []
    functional_requirements = []

    result = get_specifications_from_plain_source_tree(frid, plain_source_tree, definitions, non_functional_requirements, test_requirements, functional_requirements)
    if result is None:
        raise Exception(f"Functional requirement {frid} does not exist.")

    return {
        DEFINITIONS: definitions,
        NON_FUNCTIONAL_REQUIREMENTS: non_functional_requirements,
        TEST_REQUIREMENTS: test_requirements,
        FUNCTIONAL_REQUIREMENTS: functional_requirements
    }