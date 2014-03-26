#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Netius System
# Copyright (C) 2008-2012 Hive Solutions Lda.
#
# This file is part of Hive Netius System.
#
# Hive Netius System is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hive Netius System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hive Netius System. If not, see <http://www.gnu.org/licenses/>.

__author__ = "João Magalhães joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2012 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import base64

import netius

import asn
import util

BEGIN_PRIVATE = "-----BEGIN RSA PRIVATE KEY-----"
END_PRIVATE = "-----END RSA PRIVATE KEY-----"
BEGIN_PUBLIC = "-----BEGIN PUBLIC KEY-----"
END_PUBLIC = "-----END PUBLIC KEY-----"

RSAID_PKCS1 = "\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01"
HASHID_SHA1 = "\x2b\x0e\x03\x02\x1a"
HASHID_SHA256 = "\x60\x86\x48\x01\x65\x03\x04\x02\x01"

def open_pem_key(path, begin = BEGIN_PRIVATE, end = END_PRIVATE):
    file = open(path, "rb")
    try: data = file.read()
    finally: file.close()

    begin_index = data.find(begin)
    end_index = data.find(end)

    if begin_index == -1: raise netius.ParserError("Invalid key format")
    if end_index == -1: raise netius.ParserError("Invalid key format")

    begin_index += len(begin)

    data = data[begin_index:end_index]
    data = data.strip()
    return base64.b64decode(data)

def write_pem_key(
    path,
    data,
    begin = BEGIN_PRIVATE,
    end = END_PRIVATE,
    width = 64
):
    data = base64.b64encode(data)

    chunks = [chunk for chunk in util.chunks(data, width)]
    data = "\n".join(chunks)

    file = open(path, "wb")
    try:
        file.write(begin)
        file.write("\n")
        file.write(data)
        file.write("\n")
        file.write(end)
        file.write("\n")
    finally:
        file.close()

def open_private_key(path):
    data = open_pem_key(
        path,
        begin = BEGIN_PRIVATE,
        end = END_PRIVATE
    )
    asn1 = asn.asn1_parse(asn.ASN1_RSA_PRIVATE_KEY, data)[0]
    private_key = dict(
        version = asn1[0],
        modulus = asn1[1],
        public_exponent = asn1[2],
        private_exponent = asn1[3],
        prime1 = asn1[4],
        prime2 = asn1[5],
        exponent1 = asn1[6],
        exponent2 = asn1[7],
        coefficient = asn1[8]
    )
    return private_key

def open_public_key(path):
    data = open_pem_key(
        path,
        begin = BEGIN_PUBLIC,
        end = END_PUBLIC
    )
    asn1 = asn.asn1_parse(asn.ASN1_OBJECT, data)[0]
    asn1 = asn.asn1_parse(asn.ASN1_RSA_PUBLIC_KEY, asn1[1][1:])[0]
    public_key = dict(
        modulus = asn1[0],
        public_exponent = asn1[1]
    )
    return public_key

def write_private_key(path, private_key):
    pass

def write_public_key(path, public_key):
    data = "\x00" + asn.asn_gen(
        (asn.SEQUENCE, [
            (asn.INTEGER, public_key["modulus"]),
            (asn.INTEGER, public_key["public_exponent"])
        ])
    )
    data = asn.asn_gen(
        (asn.SEQUENCE, [
            (asn.SEQUENCE, [
                (asn.OBJECT_IDENTIFIER, RSAID_PKCS1),
                (asn.NULL, None)
            ]),
            (asn.OCTET_STRING, data)
        ])
    )
    write_pem_key(
        path,
        data,
        begin = BEGIN_PUBLIC,
        end = END_PUBLIC
    )
    
def pem_to_der(in_path, out_path, begin = BEGIN_PRIVATE, end = END_PRIVATE):
    data = open_pem_key(in_path, begin = begin, end = end)
    file = open(out_path, "wb")
    try: file.write(data)
    finally: file.close()

def private_to_public(private_key):
    public_key = dict(
        modulus = private_key["modulus"],
        public_exponent = private_key["public_exponent"]
    )
    return public_key

import pprint
pprint.pprint(open_private_key("C:/repo.extra/netius/src/netius/base/extras/net.key"))
pkey = open_public_key("C:/repo.extra/netius/src/netius/base/extras/net.pub")
print pkey

write_public_key("C:/tobias.pub", pkey)
#pkey = open_public_key("C:/tobias.pub")
#print pkey

pem_to_der("C:/repo.extra/netius/src/netius/base/extras/net.pub", "C:/net.pub.der", begin = BEGIN_PUBLIC, end = END_PUBLIC)
pem_to_der("C:/tobias.pub", "C:/tobias.pub.der", begin = BEGIN_PUBLIC, end = END_PUBLIC)
