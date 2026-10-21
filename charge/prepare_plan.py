"""Resolve scheduler and timeouts; add an explicit origin before user ramp-up."""
import argparse
import xml.etree.ElementTree as ET


def prepare(source, destination):
    tree = ET.parse(source)
    group = tree.find('.//ThreadGroup')
    group.find("./boolProp[@name='ThreadGroup.scheduler']").text = 'true'
    # Reuse TCP connections between iterations. CookieManager still clears sessions
    # before every login; CSV accounts still rotate. Avoid exhausting Windows ports.
    group.find("./boolProp[@name='ThreadGroup.same_user_on_next_iteration']").text = 'true'
    for sampler in tree.findall('.//HTTPSamplerProxy'):
        for key, value in [('HTTPSampler.connect_timeout', '5000'),
                           ('HTTPSampler.response_timeout', '30000')]:
            existing = next((x for x in sampler if x.get('name') == key), None)
            if existing is not None:
                sampler.remove(existing)
            ET.SubElement(sampler, 'stringProp', name=key).text = value
    # Successful login must create a session, not merely return HTTP 200.
    main_tree = tree.getroot().find('./hashTree/hashTree/hashTree')
    if main_tree is not None:
        children = list(main_tree)
        for i, child in enumerate(children):
            if child.tag == 'HTTPSamplerProxy' and child.get('testname') == '01 - Connexion':
                checks = children[i + 1]
                assertion = ET.SubElement(checks, 'ResponseAssertion', guiclass='AssertionGui',
                    testclass='ResponseAssertion', testname='Cookie de session present', enabled='true')
                strings = ET.SubElement(assertion, 'collectionProp', name='Asserion.test_strings')
                ET.SubElement(strings, 'stringProp', name='cookie').text = '(?i)set-cookie:.*refuges_session='
                ET.SubElement(assertion, 'stringProp', name='Assertion.test_field').text = 'Assertion.response_headers'
                ET.SubElement(assertion, 'boolProp', name='Assertion.assume_success').text = 'false'
                ET.SubElement(assertion, 'intProp', name='Assertion.test_type').text = '2'
                ET.SubElement(checks, 'hashTree')
    container = tree.getroot().find('./hashTree/hashTree')
    setup = ET.Element('SetupThreadGroup', guiclass='SetupThreadGroupGui',
                       testclass='SetupThreadGroup', testname='Origine de mesure', enabled='true')
    ET.SubElement(setup, 'stringProp', name='ThreadGroup.on_sample_error').text = 'stoptest'
    controller = ET.SubElement(setup, 'elementProp', name='ThreadGroup.main_controller',
                               elementType='LoopController', guiclass='LoopControlPanel',
                               testclass='LoopController', testname='Une fois', enabled='true')
    ET.SubElement(controller, 'boolProp', name='LoopController.continue_forever').text = 'false'
    ET.SubElement(controller, 'stringProp', name='LoopController.loops').text = '1'
    ET.SubElement(setup, 'stringProp', name='ThreadGroup.num_threads').text = '1'
    ET.SubElement(setup, 'stringProp', name='ThreadGroup.ramp_time').text = '0'
    ET.SubElement(setup, 'boolProp', name='ThreadGroup.scheduler').text = 'false'
    setup_tree = ET.Element('hashTree')
    sampler = ET.SubElement(setup_tree, 'JSR223Sampler', guiclass='TestBeanGUI',
                            testclass='JSR223Sampler', testname='__measurement_origin', enabled='true')
    ET.SubElement(sampler, 'stringProp', name='scriptLanguage').text = 'groovy'
    ET.SubElement(sampler, 'stringProp', name='cacheKey').text = 'true'
    ET.SubElement(sampler, 'stringProp', name='script').text = (
        "SampleResult.setResponseCode('200'); SampleResult.setSuccessful(true); "
        "SampleResult.setResponseMessage('Measurement origin, excluded from statistics')")
    ET.SubElement(setup_tree, 'hashTree')
    container.insert(0, setup)
    container.insert(1, setup_tree)
    tree.write(destination, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('destination')
    args = parser.parse_args()
    prepare(args.source, args.destination)
