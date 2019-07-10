#!/usr/bin/env python
import sys
import os
import json
import logging
import argparse
here = os.path.dirname(os.path.abspath(__file__))
student_dir = os.path.join(here,'../labtainer-student')
sys.path.append(os.path.join(student_dir, 'bin'))
sys.path.append(os.path.join(student_dir, 'lab_bin'))
import labutils
import LabtainerLogging
'''
Wraper functions for invoking Labtainer functions from GNS3
'''

def getLabFromImage(image_name):
    ''' strip off tag if present '''
    if ':' in image_name:
        image_name = image_name.rsplit(':', 1)[0]
    suffix = '-labtainer'
    if not image_name.endswith(suffix):
        print('%s not a labtainer' % image_name)
        return
    index = len(suffix) * -1
    lab_box = image_name[:index]
    parts = lab_box.rsplit('-', 1)
    lab = parts[0]
    box = parts[1]
    return lab, box

def labtainerTerms(images, logger):
    labutils.logger = logger
    logger.debug('labtainerTerms %d images' % len(images))
    image = next(iter(images))
    labname, box = getLabFromImage(image)
    here = os.path.dirname(os.path.abspath(__file__))
    gparent = os.path.dirname(os.path.dirname(here))
    lab_path = os.path.join(gparent, 'labs', labname)
    logger.debug('lab_path is %s' % lab_path)

    container_map = {}
    labtainer_config, start_config = labutils.GetBothConfigs(lab_path, logger)
    for name, container in start_config.containers.items():
        #print('name %s full %s' % (name, container.full_name))
        gimage = '%s-%s-labtainer' % (labname, name)
        for image in images:
            if image.startswith(gimage):
                gcontainer = images[image]
                #print('got match %s cont %s' % (image, gcontainer))
                container_map[container.full_name] = gcontainer

    labutils.DoTerminals(start_config, lab_path, container_map = container_map)

def gatherZips(zip_list, image, logger):
    labutils.logger = logger
    here = os.path.dirname(os.path.abspath(__file__))
    labname, name = getLabFromImage(image)
    parent = os.path.dirname(here)
    gparent = os.path.dirname(parent)
    lab_path = os.path.join(gparent, 'labs', labname)
    logger.debug('gatherZips lab_path is %s' % lab_path)
    labtainer_config, start_config = labutils.GetBothConfigs(lab_path, logger)
    labutils.GatherZips(zip_list, labtainer_config, start_config, labname, lab_path)

def labtainerStop(image, container_id, logger):
    labutils.logger = logger
    here = os.path.dirname(os.path.abspath(__file__))
    labname, name = getLabFromImage(image)
    parent = os.path.dirname(here)
    gparent = os.path.dirname(parent)
    lab_path = os.path.join(gparent, 'labs', labname)
    logger.debug('labtainerStop lab_path is %s' % lab_path)
    labtainer_config, start_config = labutils.GetBothConfigs(lab_path, logger)
    here = os.getcwd()
    student_dir = os.path.join(parent, 'labtainer-student')
    os.chdir(student_dir)
    for name, container in start_config.containers.items():
        logger.debug('name %s full %s' % (name, container.full_name))
        gimage = '%s-%s-labtainer' % (labname, name)
        if image.startswith(gimage):

            labutils.GatherOtherArtifacts(lab_path, name, container_id, container.user, container.password, True)
            base_file_name, zip_file_name = labutils.CreateCopyChownZip(start_config, labtainer_config, name,
                             container.full_name, container.image_name, container.user, container.password, True, True, running_container=container_id)
    os.chdir(here)
    return zip_file_name

def parameterizeOne(image_name, logger):
    labutils.logger = logger

    here = os.path.dirname(os.path.abspath(__file__))
    labname, comp_name = getLabFromImage(image_name)
    parent = os.path.dirname(here)
    gparent = os.path.dirname(parent)
    lab_path = os.path.join(gparent, 'labs', labname)
    logger.debug('paremterizeOne lab_path is %s' % lab_path)
    labtainer_config, start_config = labutils.GetBothConfigs(lab_path, logger)
    running = labutils.GetContainerId(image_name)
    logger.debug('running is %s  ' % running)
    email_addr = labutils.getLastEmail()
    if email_addr is None:
        logger.error('Missing labtainer email address')
        ''' TBD dialog?  Tell user how to add it '''
        return
    for name, container in start_config.containers.items():
        if name == comp_name:
                logger.debug('found match container name %s' % name)
                labutils.ParamForStudent(start_config.lab_master_seed, container.full_name, container.user, container.password,
                                labname, email_addr, lab_path, name, None, running_container = running)
                return

if __name__ == '__main__':
    home = os.getenv("HOME")
    gns3_path = os.path.join(home, 'GNS3', 'projects')
    logger = LabtainerLogging.LabtainerLogging("test.log", 'eh', "../../config/labtainer.config")
    parser = argparse.ArgumentParser(description='Generate gns3 network interfaces file.')
    parser.add_argument('labname', help='Name of labtainers lab')
    parser.add_argument('gns3_proj', help='Name of gns3 project')
    parser.add_argument('fun', help='Name of function to test') 
    args = parser.parse_args()
    
    gns3_proj = os.path.join(gns3_path, args.gns3_proj, args.gns3_proj+'.gns3')
    if args.fun == 'term':
        images = {}
        with open(gns3_proj) as fh:
            gns3_json = json.load(fh)
            for node in gns3_json['topology']['nodes']:
                image = node['properties']['image']
                images[image] = node['properties']['container_id']
        labtainerTerms(images, logger)
    elif args.fun == 'stop':
        image = None
        zip_file_list = []
        with open(gns3_proj) as fh:
            gns3_json = json.load(fh)
            for node in gns3_json['topology']['nodes']:
                image = node['properties']['image']
                if 'labtainer' in image:
                    labname, box = getLabFromImage(image)
                    container_id = node['properties']['container_id']
                    zip_file = labtainerStop(image, container_id, logger)
                    if zip_file is None:
                        logger.error('zipfile is none for image %s  is it running?' % image)
                        exit(1)
                    zip_file_list.append(zip_file)
        if len(zip_file_list) > 0:
            gatherZips(zip_file_list, image, logger)
        else:
            print('No zipfiles found, are containers running?')
    elif args.fun == 'param':
        image = None
        with open(gns3_proj) as fh:
            gns3_json = json.load(fh)
            for node in gns3_json['topology']['nodes']:
                image = node['properties']['image']
                if 'labtainer' in image:
                    parameterizeOne(image, logger)
