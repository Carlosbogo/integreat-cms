import logging
from urllib.parse import urlparse

from django.core.serializers import base

from ..cms.models import Page, PageTranslation, Language

from . import base_serializer


logger = logging.getLogger(__name__)


class Serializer(base_serializer.Serializer):
    """
    XLIFF serializer class for XLIFF version 1.2.
    This was inspired by `django-xliff <https://github.com/callowayproject/django-xliff>`__.
    """

    def start_serialization(self):
        """
        Start serialization - open the XML document and the root element.
        """
        super().start_serialization()
        self.xml.startElement(
            "xliff",
            {
                "version": "1.2",
                "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
            },
        )

    def start_object(self, obj):
        """
        Called as each object is handled. Adds an XLIFF ``<file>``-block with meta-information about the object and an
        additional ``<body>`` for XLIFF version 1.2.

        :param obj: The page translation object which is started
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :raises ~django.core.serializers.base.SerializationError: If the serialization fails
        """
        source_language = obj.language.get_source_language(obj.page.region)
        if not source_language:
            raise base.SerializationError(
                "The page translation is in the region's default language."
            )
        self.xml.startElement(
            "file",
            {
                "original": str(obj.page.id),
                "datatype": "plaintext",
                "source-language": source_language.slug,
                "target-language": obj.language.slug,
            },
        )
        self.xml.startElement("body", {})

    def handle_field(self, obj, field):
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)

        :param obj: The page translation object which is handled
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        :param field: The model field
        :type field: ~django.db.models.Field
        """
        attrs = {
            "id": field.name,
            "resname": field.name,
            "restype": "string",
            "datatype": "html",
        }
        self.xml.startElement("trans-unit", attrs)

        self.xml.startElement("source", {})
        source_translation = obj.source_translation
        self.xml.cdata(field.value_to_string(source_translation))
        self.xml.endElement("source")

        self.xml.startElement("target", {})
        self.xml.cdata(field.value_to_string(obj))
        self.xml.endElement("target")

        self.xml.endElement("trans-unit")

    def end_object(self, obj):
        """
        Called after handling all fields for an object.
        Ends the ``<file>``-block.

        :param obj: The page translation object which is finished
        :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation
        """
        self.xml.endElement("body")
        self.xml.endElement("file")


# pylint: disable=too-few-public-methods
class Deserializer(base_serializer.Deserializer):
    """
    XLIFF deserializer class for XLIFF version 1.2
    """

    #: The node name of serialized fields
    unit_node = "trans-unit"

    def get_object(self, node):
        """
        Retrieve an object from the serialized unit node.

        :param node: The current xml node of the object
        :type node: xml.dom.minidom.Element

        :raises ~django.core.serializers.base.DeserializationError: If the deserialization fails

        :return: The original page translation
        :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

        """
        # Get original page
        page_id = self.require_attribute(node, "original")
        try:
            page = Page.objects.get(id=page_id)
        except (ValueError, Page.DoesNotExist) as e:
            # If the id isn't a number or if no page with this id is found, check if the external file reference is given
            external_file = node.getElementsByTagName("external-file")
            if not external_file:
                # If no such reference is given, just raise the initial error
                raise e
            # Get href of external file and parse url
            page_link = (
                urlparse(self.require_attribute(external_file[0], "href"))
                .path.strip("/")
                .split("/")
            )
            logger.debug(
                "<external-file>-node found, parsed page link: %r",
                page_link,
            )
            # Expect the link to be in the format /<region_slug>/<language_slug>/[<parent_page_slug>]/<page_slug>/
            if len(page_link) < 3:
                raise base.DeserializationError(
                    "The page link of the <external-file> reference needs at least 3 segments"
                ) from e
            page_translation_slug = page_link.pop()
            region_slug, language_slug = page_link[:2]
            page = Page.objects.get(
                region__slug=region_slug,
                translations__slug=page_translation_slug,
                translations__language__slug=language_slug,
            )

        logger.debug(
            "Referenced original page: %r",
            page,
        )

        # Get target language of this file
        target_language_slug = self.require_attribute(node, "target-language")

        # Get existing target translation or create a new one
        page_translation = page.get_translation(
            target_language_slug
        ) or PageTranslation(
            page=page,
            language=Language.objects.get(slug=target_language_slug),
        )
        return page_translation
