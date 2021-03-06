import json
import operator

from operator import attrgetter
from distutils.version import LooseVersion

from core.models import PlCoreBase, PlCoreBaseManager, SingletonModel, XOS
from core.models.plcorebase import StrippedCharField
from django.db import models
from django.core.validators import URLValidator
from xos.exceptions import *
import urlparse

COARSE_KIND = "coarse"

def get_xos():
    xos = XOS.objects.all()

    if xos:
       return xos[0]
    else:
       return None

class AttributeMixin(object):
    # helper for extracting things from a json-encoded
    # service_specific_attribute

    def get_attribute(self, name, default=None):
        if self.service_specific_attribute:
            attributes = json.loads(self.service_specific_attribute)
        else:
            attributes = {}
        return attributes.get(name, default)

    def set_attribute(self, name, value):
        if self.service_specific_attribute:
            attributes = json.loads(self.service_specific_attribute)
        else:
            attributes = {}
        attributes[name] = value
        self.service_specific_attribute = json.dumps(attributes)

    def get_initial_attribute(self, name, default=None):
        if self._initial["service_specific_attribute"]:
            attributes = json.loads(
                self._initial["service_specific_attribute"])
        else:
            attributes = {}
        return attributes.get(name, default)

    @classmethod
    def get_default_attribute(cls, name):
        for (attrname, default) in cls.simple_attributes:
            if attrname == name:
                return default
        if hasattr(cls, "default_attributes"):
            if name in cls.default_attributes:
                return cls.default_attributes[name]

        return None

    @classmethod
    def setup_simple_attributes(cls):
        for (attrname, default) in cls.simple_attributes:
            setattr(cls, attrname, property(lambda self, attrname=attrname, default=default: self.get_attribute(attrname, default),
                                            lambda self, value, attrname=attrname: self.set_attribute(
                                                attrname, value),
                                            None,
                                            attrname))

class LoadableModule(PlCoreBase):
    xos = models.ForeignKey(XOS, related_name='loadable_modules', help_text="Pointer to XOS", default=get_xos)
    name = StrippedCharField(max_length=30, help_text="Service Name")
    base_url = StrippedCharField(max_length=1024, help_text="Base URL, allows use of relative URLs for resources", null=True, blank=True)

    version = StrippedCharField(blank=True, null=True,
        max_length=30, help_text="Version of Service Controller", default = "1.0.0")
    provides = StrippedCharField(blank=True, null=True,
        max_length=254, help_text="Comma-separated list of things provided")
    requires = StrippedCharField(blank=True, null=True,
        max_length=254, help_text="Comma-separated list of required Service Controllers")

    def __unicode__(self): return u'%s' % (self.name)

    def save(self, *args, **kwargs):
       super(LoadableModule, self).save(*args, **kwargs)

       # This is necessary, as the XOS syncstep handles rerunning the docker-
       # compose.
       # TODO: Update synchronizer and replace with watcher functionality
       if self.xos:
           # force XOS to rebuild
           self.xos.save(update_fields=["updated"])

    def get_provides_list(self):
        prov_list = []
        if self.provides and self.provides.strip():
            for prov in self.provides.split(","):
                prov=prov.strip()
                if "=" in prov:
                    (name, version) = prov.split("=",1)
                    name = name.strip()
                    version = version.strip()
                else:
                    name = prov
                    version = "1.0.0"
                prov_list.append( {"name": name, "version": version} )

        # every controller provides itself
        prov_list.append( {"name": self.name, "version": self.version} )

        return prov_list


    @classmethod
    def dependency_check(cls, dep_list):
        missing = []
        satisfied = []
        operators = {">=": operator.ge,
                     "<=": operator.le,
                     ">": operator.gt,
                     "<": operator.lt,
                     "!=": operator.ne,
                     "=": operator.eq}
        for dep in dep_list:
            dep = dep.strip()
            name = dep
            version = None
            this_op = None
            for op in operators.keys():
                if op in dep:
                    (name, version) = dep.split(op,1)
                    name = name.strip()
                    version = version.strip()
                    this_op = operators[op]
                    break
            found=False
            scs = ServiceController.objects.all()
            for sc in scs:
                for provide in sc.get_provides_list():
                    if (provide["name"] != name):
                        continue
                    if not this_op:
                        satisfied.append(sc)
                        found=True
                        break
                    elif this_op(LooseVersion(provide["version"]), LooseVersion(version)):
                        satisfied.append(sc)
                        found=True
                        break
            if not found:
                missing.append(dep)

        return (satisfied, missing)

class LoadableModuleResource(PlCoreBase):
    KIND_CHOICES = (('models', 'Models'),
                    ('admin', 'Admin'),
                    ('admin_template', 'Admin Template'),
                    ('django_library', 'Django Library'),
                    ('synchronizer', 'Synchronizer'),
                    ('rest_service', 'REST API (service)'),
                    ('rest_tenant', 'REST API (tenant)'),
                    ('tosca_custom_types', 'Tosca Custom Types'),
                    ('tosca_resource', 'Tosca Resource'),
                    ('private_key', 'Private Key'),
                    ('public_key', 'Public Key'),
                    ('vendor_js', 'Vendor Javascript'))

    FORMAT_CHOICES = (('python', 'Python'),
                      ('manifest', 'Manifest'),
                      ('docker', 'Docker Container'),
                      ('yaml', 'YAML'),
                      ('raw', 'raw'),
                      ('javascript', 'Javascript'))

    loadable_module = models.ForeignKey(LoadableModule, related_name='loadable_module_resources',
                                help_text="The Loadable Module this resource is associated with")

    name = StrippedCharField(max_length=30, help_text="Object Name")
    subdirectory = StrippedCharField(max_length=1024, help_text="optional subdirectory", null=True, blank=True)
    kind = StrippedCharField(choices=KIND_CHOICES, max_length=30)
    format = StrippedCharField(choices=FORMAT_CHOICES, max_length=30)
    url = StrippedCharField(max_length=1024, help_text="URL of resource", null=True, blank=True)

    def __unicode__(self): return u'%s' % (self.name)

    @property
    def full_url(self):
        if self.loadable_module and self.loadable_module.base_url:
            return urlparse.urljoin(self.loadable_module.base_url, self.url)
        else:
            return self.url

class Library(LoadableModule):
    # for now, it's exactly like a LoadableModule
    pass


class XOSComponent(LoadableModule):
    # this will define loadable XOS component in the form of containers
    image = StrippedCharField(max_length=200, help_text="docker image name")
    command = StrippedCharField(max_length=1024, help_text="docker run command", null=True, blank=True)
    ports = StrippedCharField(max_length=200, help_text="port binding", null=True, blank=True)
    extra = StrippedCharField(max_length=200, help_text="extra information needed by containers", null=True, blank=True)

    no_start = models.BooleanField(help_text="Do not start the Component", default=False)


class XOSComponentLink(PlCoreBase):

    LINK_KIND = (
        ('internal', 'Internal'),
        ('external', 'External')
    )

    component = models.ForeignKey(XOSComponent, related_name='links', help_text="The Component object for this Link")
    container = StrippedCharField(max_length=200, help_text="container to link")
    alias = StrippedCharField(max_length=200, help_text="alias for the link")
    kind = models.CharField(max_length=20, choices=LINK_KIND, default='internal')

    def save(self, *args, **kwds):
        existing = XOSComponentLink.objects.filter(container=self.container, alias=self.alias)
        if len(existing) > 0:
            raise XOSValidationError('XOSComponentLink for %s:%s already defined' % (self.container, self.alias))
        super(XOSComponentLink, self).save(*args, **kwds)


# NOTE can this be the same of XOSVolume??
class XOSComponentVolume(PlCoreBase):
    component = models.ForeignKey(XOSComponent, related_name='volumes', help_text="The Component object for this Volume")
    name = StrippedCharField(max_length=300, help_text="Volume Name")
    container_path = StrippedCharField(max_length=1024, unique=True, help_text="Path of Volume in Container")
    host_path = StrippedCharField(max_length=1024, help_text="Path of Volume in Host")
    read_only = models.BooleanField(default=False, help_text="True if mount read-only")

    def save(self, *args, **kwds):
        existing = XOSComponentVolume.objects.filter(container_path=self.container_path, host_path=self.host_path)
        if len(existing) > 0:
            raise XOSValidationError('XOSComponentVolume for %s:%s already defined' % (self.container_path, self.host_path))
        super(XOSComponentVolume, self).save(*args, **kwds)


class XOSComponentVolumeContainer(PlCoreBase):
    component = models.ForeignKey(XOSComponent, related_name='volumecontainers', help_text="The Component object for this VolumeContainer")
    name = StrippedCharField(max_length=300, help_text="Volume Name")
    container = StrippedCharField(max_length=300, help_text="Volume Name")

    def save(self, *args, **kwds):
        existing = XOSComponentVolumeContainer.objects.filter(name=self.name)
        if len(existing) > 0:
            raise XOSValidationError('XOSComponentVolumeContainer for %s:%s already defined' % (self.container_path, self.host_path))
        super(XOSComponentVolumeContainer, self).save(*args, **kwds)


class ServiceController(LoadableModule):
    synchronizer_run = StrippedCharField(max_length=1024, help_text="synchronizer run command", null=True, blank=True)
    synchronizer_config = StrippedCharField(max_length=1024, help_text="synchronizer config file", null=True, blank=True)

    no_start = models.BooleanField(help_text="Do not start the Synchronizer", default=False)

class ServiceControllerResource(LoadableModuleResource):
    class Meta:
        proxy = True

class Service(PlCoreBase, AttributeMixin):
    # when subclassing a service, redefine KIND to describe the new service
    KIND = "generic"

    description = models.TextField(
        max_length=254, null=True, blank=True, help_text="Description of Service")
    enabled = models.BooleanField(default=True)
    kind = StrippedCharField(
        max_length=30, help_text="Kind of service", default=KIND)
    name = StrippedCharField(max_length=30, help_text="Service Name")
    versionNumber = StrippedCharField(blank=True, null=True,
        max_length=30, help_text="Version of Service Definition")   # deprecated
    published = models.BooleanField(default=True)
    view_url = StrippedCharField(blank=True, null=True, max_length=1024)
    icon_url = StrippedCharField(blank=True, null=True, max_length=1024)
    public_key = models.TextField(
        null=True, blank=True, max_length=1024, help_text="Public key string")
    private_key_fn = StrippedCharField(blank=True, null=True, max_length=1024)

    # Service_specific_attribute and service_specific_id are opaque to XOS
    service_specific_id = StrippedCharField(
        max_length=30, blank=True, null=True)
    service_specific_attribute = models.TextField(blank=True, null=True)

    controller = models.ForeignKey(ServiceController, related_name='services',
                                help_text="The Service Controller this Service uses",
                                null=True, blank=True)

    def __init__(self, *args, **kwargs):
        # for subclasses, set the default kind appropriately
        self._meta.get_field("kind").default = self.KIND
        super(Service, self).__init__(*args, **kwargs)

    @classmethod
    def get_service_objects(cls):
        return cls.objects.filter(kind=cls.KIND)

    @classmethod
    def get_deleted_service_objects(cls):
        return cls.deleted_objects.filter(kind=cls.KIND)

    @classmethod
    def get_service_objects_by_user(cls, user):
        return cls.select_by_user(user).filter(kind=cls.KIND)

    @classmethod
    def select_by_user(cls, user):
        if user.is_admin:
            return cls.objects.all()
        else:
            service_ids = [
                sp.slice.id for sp in ServicePrivilege.objects.filter(user=user)]
            return cls.objects.filter(id__in=service_ids)

    @property
    def serviceattribute_dict(self):
        attrs = {}
        for attr in self.serviceattributes.all():
            attrs[attr.name] = attr.value
        return attrs

    def __unicode__(self): return u'%s' % (self.name)

    def can_update(self, user):
        return user.can_update_service(self, allow=['admin'])

    def get_scalable_nodes(self, slice, max_per_node=None, exclusive_slices=[]):
        """
             Get a list of nodes that can be used to scale up a slice.

                slice - slice to scale up
                max_per_node - maximum numbers of instances that 'slice' can have on a single node
                exclusive_slices - list of slices that must have no nodes in common with 'slice'.
        """

        # late import to get around order-of-imports constraint in __init__.py
        from core.models import Node, Instance

        nodes = list(Node.objects.all())

        conflicting_instances = Instance.objects.filter(
            slice__in=exclusive_slices)
        conflicting_nodes = Node.objects.filter(
            instances__in=conflicting_instances)

        nodes = [x for x in nodes if x not in conflicting_nodes]

        # If max_per_node is set, then limit the number of instances this slice
        # can have on a single node.
        if max_per_node:
            acceptable_nodes = []
            for node in nodes:
                existing_count = node.instances.filter(slice=slice).count()
                if existing_count < max_per_node:
                    acceptable_nodes.append(node)
            nodes = acceptable_nodes

        return nodes

    def pick_node(self, slice, max_per_node=None, exclusive_slices=[]):
        # Pick the best node to scale up a slice.

        nodes = self.get_scalable_nodes(slice, max_per_node, exclusive_slices)
        nodes = sorted(nodes, key=lambda node: node.instances.all().count())
        if not nodes:
            return None
        return nodes[0]

    def adjust_scale(self, slice_hint, scale, max_per_node=None, exclusive_slices=[]):
        # late import to get around order-of-imports constraint in __init__.py
        from core.models import Instance

        slices = [x for x in self.slices.all() if slice_hint in x.name]
        for slice in slices:
            while slice.instances.all().count() > scale:
                s = slice.instances.all()[0]
                # print "drop instance", s
                s.delete()

            while slice.instances.all().count() < scale:
                node = self.pick_node(slice, max_per_node, exclusive_slices)
                if not node:
                    # no more available nodes
                    break

                image = slice.default_image
                if not image:
                    raise XOSConfigurationError(
                        "No default_image for slice %s" % slice.name)

                flavor = slice.default_flavor
                if not flavor:
                    raise XOSConfigurationError(
                        "No default_flavor for slice %s" % slice.name)

                s = Instance(slice=slice,
                             node=node,
                             creator=slice.creator,
                             image=image,
                             flavor=flavor,
                             deployment=node.site_deployment.deployment)
                s.save()

                # print "add instance", s

    def get_vtn_src_nets(self):
        nets = []
        for slice in self.slices.all():
            for ns in slice.networkslices.all():
                if not ns.network:
                    continue
#                if ns.network.template.access in ["direct", "indirect"]:
#                    # skip access networks; we want to use the private network
#                    continue
                if "management" in ns.network.name:
                    # don't try to connect the management network to anything
                    continue
                if ns.network.name in ["wan_network", "lan_network"]:
                    # we don't want to attach to the vCPE's lan or wan network
                    # we only want to attach to its private network
                    # TODO: fix hard-coding of network name
                    continue
                for cn in ns.network.controllernetworks.all():
                    if cn.net_id:
                        net = {"name": ns.network.name, "net_id": cn.net_id}
                        nets.append(net)
        return nets

    def get_vtn_nets(self):
        nets = []
        for slice in self.slices.all():
            for ns in slice.networkslices.all():
                if not ns.network:
                    continue
                if ns.network.template.access not in ["direct", "indirect"]:
                    # skip anything that's not an access network
                    continue
                for cn in ns.network.controllernetworks.all():
                    if cn.net_id:
                        net = {"name": ns.network.name, "net_id": cn.net_id}
                        nets.append(net)
        return nets

    def get_vtn_dependencies_nets(self):
        provider_nets = []
        for tenant in self.subscribed_tenants.all():
            if tenant.provider_service:
                for net in tenant.provider_service.get_vtn_nets():
                    if not net in provider_nets:
                        net["bidirectional"] = tenant.connect_method!="private-unidirectional"
                        provider_nets.append(net)
        return provider_nets

    def get_vtn_dependencies_ids(self):
        return [x["net_id"] for x in self.get_vtn_dependencies_nets()]

    def get_vtn_dependencies_names(self):
        return [x["name"] + "_" + x["net_id"] for x in self.get_vtn_dependencies_nets()]

    def get_vtn_src_ids(self):
        return [x["net_id"] for x in self.get_vtn_src_nets()]

    def get_vtn_src_names(self):
        return [x["name"] + "_" + x["net_id"] for x in self.get_vtn_src_nets()]

    def get_composable_networks(self):
	SUPPORTED_VTN_SERVCOMP_KINDS = ['VSG','PRIVATE']

        nets = []
        for slice in self.slices.all():
            for net in slice.networks.all():
                if (net.template.vtn_kind not in SUPPORTED_VTN_SERVCOMP_KINDS) or (net.owner != slice):
                    continue

                if not net.controllernetworks.exists():
                    continue
                nets.append(net)
        return nets


class ServiceAttribute(PlCoreBase):
    name = models.CharField(help_text="Attribute Name", max_length=128)
    value = models.TextField(help_text="Attribute Value")
    service = models.ForeignKey(Service, related_name='serviceattributes',
                                help_text="The Service this attribute is associated with")


class ServiceRole(PlCoreBase):
    ROLE_CHOICES = (('admin', 'Admin'),)
    role = StrippedCharField(choices=ROLE_CHOICES, unique=True, max_length=30)

    def __unicode__(self): return u'%s' % (self.role)


class ServicePrivilege(PlCoreBase):
    user = models.ForeignKey('User', related_name='serviceprivileges')
    service = models.ForeignKey('Service', related_name='serviceprivileges')
    role = models.ForeignKey('ServiceRole', related_name='serviceprivileges')

    class Meta:
        unique_together = ('user', 'service', 'role')

    def __unicode__(self): return u'%s %s %s' % (
        self.service, self.user, self.role)

    def can_update(self, user):
        if not self.service.enabled:
            raise PermissionDenied, "Cannot modify permission(s) of a disabled service"
        return self.service.can_update(user)

    def save(self, *args, **kwds):
        if not self.service.enabled:
            raise PermissionDenied, "Cannot modify permission(s) of a disabled service"
        super(ServicePrivilege, self).save(*args, **kwds)

    def delete(self, *args, **kwds):
        if not self.service.enabled:
            raise PermissionDenied, "Cannot modify permission(s) of a disabled service"
        super(ServicePrivilege, self).delete(*args, **kwds)

    @classmethod
    def select_by_user(cls, user):
        if user.is_admin:
            qs = cls.objects.all()
        else:
            qs = cls.objects.filter(user=user)
        return qs

#Model that defines the information needed to enable monitoring agents of a service
class ServiceMonitoringAgentInfo(PlCoreBase):
    name = models.CharField(help_text="Monitoring Agent Name", max_length=128)
    service = models.ForeignKey(Service, related_name='servicemonitoringagents', blank=True, null=True,
                                help_text="The Service this attribute is associated with")
    target_uri = models.TextField(validators=[URLValidator()], help_text="Monitoring collector URI to be used by agents to publish the data")


class TenantRoot(PlCoreBase, AttributeMixin):
    """ A tenantRoot is one of the things that can sit at the root of a chain
        of tenancy. This object represents a node.
    """

    KIND = "generic"
    kind = StrippedCharField(max_length=30, default=KIND)
    name = StrippedCharField(
        max_length=255, help_text="name", blank=True, null=True)

    service_specific_attribute = models.TextField(blank=True, null=True)
    service_specific_id = StrippedCharField(
        max_length=30, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        # for subclasses, set the default kind appropriately
        self._meta.get_field("kind").default = self.KIND
        super(TenantRoot, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if not self.name:
            return u"%s-tenant_root-#%s" % (str(self.kind), str(self.id))
        else:
            return self.name

    def can_update(self, user):
        return user.can_update_tenant_root(self, allow=['admin'])

    def get_subscribed_tenants(self, tenant_class):
        ids = self.subscribed_tenants.filter(kind=tenant_class.KIND)
        return tenant_class.objects.filter(id__in=ids)

    def get_newest_subscribed_tenant(self, kind):
        st = list(self.get_subscribed_tenants(kind))
        if not st:
            return None
        return sorted(st, key=attrgetter('id'))[0]

    @classmethod
    def get_tenant_objects(cls):
        return cls.objects.filter(kind=cls.KIND)

    @classmethod
    def get_tenant_objects_by_user(cls, user):
        return cls.select_by_user(user).filter(kind=cls.KIND)

    @classmethod
    def select_by_user(cls, user):
        if user.is_admin:
            return cls.objects.all()
        else:
            tr_ids = [
                trp.tenant_root.id for trp in TenantRootPrivilege.objects.filter(user=user)]
            return cls.objects.filter(id__in=tr_ids)

    # helper function to be used in subclasses that want to ensure
    # service_specific_id is unique
    def validate_unique_service_specific_id(self, none_okay=False):
        if not none_okay and (self.service_specific_id is None):
            raise XOSMissingField("subscriber_specific_id is None, and it's a required field", fields={
                                  "service_specific_id": "cannot be none"})

        if self.service_specific_id:
            conflicts = self.get_tenant_objects().filter(
                service_specific_id=self.service_specific_id)
            if self.pk:
                conflicts = conflicts.exclude(pk=self.pk)
            if conflicts:
                raise XOSDuplicateKey("service_specific_id %s already exists" % self.service_specific_id, fields={
                                      "service_specific_id": "duplicate key"})


class Tenant(PlCoreBase, AttributeMixin):
    """ A tenant is a relationship between two entities, a subscriber and a
        provider. This object represents an edge.

        The subscriber can be a User, a Service, or a Tenant.

        The provider is always a Service.

        TODO: rename "Tenant" to "Tenancy"
    """

    CONNECTIVITY_CHOICES = (('public', 'Public'),
                            ('private', 'Private'),
                            ('private-unidirectional', 'Private Unidirectional'),
                            ('na', 'Not Applicable'))

    # when subclassing a service, redefine KIND to describe the new service
    KIND = "generic"

    kind = StrippedCharField(max_length=30, default=KIND)
    provider_service = models.ForeignKey(
        Service, related_name='provided_tenants')

    # The next four things are the various type of objects that can be subscribers of this Tenancy
    # relationship. One and only one can be used at a time.
    # XXX these should really be changed to GenericForeignKey
    subscriber_service = models.ForeignKey(
        Service, related_name='subscribed_tenants', blank=True, null=True)
    subscriber_tenant = models.ForeignKey(
        "Tenant", related_name='subscribed_tenants', blank=True, null=True)
    subscriber_user = models.ForeignKey(
        "User", related_name='subscribed_tenants', blank=True, null=True)
    subscriber_root = models.ForeignKey(
        "TenantRoot", related_name="subscribed_tenants", blank=True, null=True)
    subscriber_network = models.ForeignKey(
        "Network", related_name="subscribed_tenants", blank=True, null=True)

    # Service_specific_attribute and service_specific_id are opaque to XOS
    service_specific_id = StrippedCharField(
        max_length=30, blank=True, null=True)
    service_specific_attribute = models.TextField(blank=True, null=True)

    # Connect_method is only used by Coarse tenants
    connect_method = models.CharField(
        null=False, blank=False, max_length=30, choices=CONNECTIVITY_CHOICES, default="na")

    def __init__(self, *args, **kwargs):
        # for subclasses, set the default kind appropriately
        self._meta.get_field("kind").default = self.KIND
        super(Tenant, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u"%s-tenant-%s" % (str(self.kind), str(self.id))

    @classmethod
    def get_tenant_objects(cls):
        return cls.objects.filter(kind=cls.KIND)

    @classmethod
    def get_tenant_objects_by_user(cls, user):
        return cls.select_by_user(user).filter(kind=cls.KIND)

    @classmethod
    def get_deleted_tenant_objects(cls):
        return cls.deleted_objects.filter(kind=cls.KIND)

    @property
    def tenantattribute_dict(self):
        attrs = {}
        for attr in self.tenantattributes.all():
            attrs[attr.name] = attr.value
        return attrs

    # helper function to be used in subclasses that want to ensure
    # service_specific_id is unique
    def validate_unique_service_specific_id(self):
        if self.pk is None:
            if self.service_specific_id is None:
                raise XOSMissingField("subscriber_specific_id is None, and it's a required field", fields={
                                      "service_specific_id": "cannot be none"})

            conflicts = self.get_tenant_objects().filter(
                service_specific_id=self.service_specific_id)
            if conflicts:
                raise XOSDuplicateKey("service_specific_id %s already exists" % self.service_specific_id, fields={
                                      "service_specific_id": "duplicate key"})

    def save(self, *args, **kwargs):
        subCount = sum([1 for e in [self.subscriber_service, self.subscriber_tenant,
                                    self.subscriber_user, self.subscriber_root] if e is not None])
        if (subCount > 1):
            raise XOSConflictingField(
                "Only one of subscriber_service, subscriber_tenant, subscriber_user, subscriber_root should be set")

        super(Tenant, self).save(*args, **kwargs)

    def get_subscribed_tenants(self, tenant_class):
        ids = self.subscribed_tenants.filter(kind=tenant_class.KIND)
        return tenant_class.objects.filter(id__in=ids)

    def get_newest_subscribed_tenant(self, kind):
        st = list(self.get_subscribed_tenants(kind))
        if not st:
            return None
        return sorted(st, key=attrgetter('id'))[0]


class Scheduler(object):
    # XOS Scheduler Abstract Base Class
    # Used to implement schedulers that pick which node to put instances on

    def __init__(self, slice):
        self.slice = slice

    def pick(self):
        # this method should return a tuple (node, parent)
        #    node is the node to instantiate on
        #    parent is for container_vm instances only, and is the VM that will
        #      hold the container

        raise Exception("Abstract Base")


class LeastLoadedNodeScheduler(Scheduler):
    # This scheduler always return the node with the fewest number of
    # instances.

    def __init__(self, slice, label=None):
        super(LeastLoadedNodeScheduler, self).__init__(slice)
        self.label = label

    def pick(self):
        from core.models import Node

        # start with all nodes
        nodes = Node.objects.all()

        # if a label is set, then filter by label
        if self.label:
            nodes = nodes.filter(nodelabels__name=self.label)

        # if slice.default_node is set, then filter by default_node
        if self.slice.default_node:
            nodes = nodes.filter(name = self.slice.default_node)

        # convert to list
        nodes = list(nodes)

        # sort so that we pick the least-loaded node
        nodes = sorted(nodes, key=lambda node: node.instances.all().count())

        if not nodes:
            raise Exception(
                "LeastLoadedNodeScheduler: No suitable nodes to pick from")

        # TODO: logic to filter nodes by which nodes are up, and which
        #   nodes the slice can instantiate on.
#        nodes = sorted(nodes, key=lambda node: node.instances.all().count())
        return [nodes[0], None]


class ContainerVmScheduler(Scheduler):
    # This scheduler picks a VM in the slice with the fewest containers inside
    # of it. If no VMs are suitable, then it creates a VM.

    MAX_VM_PER_CONTAINER = 10

    def __init__(self, slice):
        super(ContainerVmScheduler, self).__init__(slice)

    @property
    def image(self):
        from core.models import Image

        # If slice has default_image set then use it
        if self.slice.default_image:
            return self.slice.default_image

        raise XOSProgrammingError("Please set a default image for %s" % self.slice.name)

    def make_new_instance(self):
        from core.models import Instance, Flavor

        flavors = Flavor.objects.filter(name="m1.small")
        if not flavors:
            raise XOSConfigurationError("No m1.small flavor")

        (node, parent) = LeastLoadedNodeScheduler(self.slice).pick()

        instance = Instance(slice=self.slice,
                            node=node,
                            image=self.image,
                            creator=self.slice.creator,
                            deployment=node.site_deployment.deployment,
                            flavor=flavors[0],
                            isolation="vm",
                            parent=parent)
        instance.save()
        # We rely on a special naming convention to identify the VMs that will
        # hole containers.
        instance.name = "%s-outer-%s" % (instance.slice.name, instance.id)
        instance.save()
        return instance

    def pick(self):
        from core.models import Instance, Flavor

        for vm in self.slice.instances.filter(isolation="vm"):
            avail_vms = []
            if (vm.name.startswith("%s-outer-" % self.slice.name)):
                container_count = Instance.objects.filter(parent=vm).count()
                if (container_count < self.MAX_VM_PER_CONTAINER):
                    avail_vms.append((vm, container_count))
            # sort by least containers-per-vm
            avail_vms = sorted(avail_vms, key=lambda x: x[1])
            print "XXX", avail_vms
            if avail_vms:
                instance = avail_vms[0][0]
                return (instance.node, instance)

        instance = self.make_new_instance()
        return (instance.node, instance)


class TenantWithContainer(Tenant):
    """ A tenant that manages an Instance
        Note: Should probably be called TenantWithInstance instead of TenantWithContainer
    """

    instance = models.ForeignKey("Instance", related_name='+', help_text="Instance used by this Tenant", null=True, blank=True)
    creator = models.ForeignKey("User", related_name='+', help_text="Creator of this Tenant", null=True, blank=True)
    external_hostname = StrippedCharField(max_length=30, help_text="External host name", null=True, blank=True) # is this still used?
    external_container = StrippedCharField(max_length=30, help_text="External host name", null=True, blank=True) # is this still used?

    def __init__(self, *args, **kwargs):
        super(TenantWithContainer, self).__init__(*args, **kwargs)

        # vSG service relies on knowing when instance id has changed
        self.orig_instance_id = self.get_attribute("instance_id")

    # vSG service relies on instance_id attribute
    def get_attribute(self, name, default=None):
        if name=="instance_id":
            if self.instance:
                return self.instance.id
            else:
                return None
        else:
            return super(TenantWithContainer, self).get_attribute(name, default)

    # Services may wish to override the image() function to return different
    # images based on criteria in the tenant object. For example,
    #    if (self.has_feature_A):
    #        return Instance.object.get(name="image_with_feature_a")
    #    elif (self.has_feature_B):
    #        return Instance.object.get(name="image_with_feature_b")
    #    else:
    #        return super(MyTenantClass,self).image()

    @property
    def image(self):
        from core.models import Image
        # Implement the logic here to pick the image that should be used when
        # instantiating the VM that will hold the container.

        slice = self.provider_service.slices.all()
        if not slice:
            raise XOSProgrammingError("provider service has no slice")
        slice = slice[0]

        # If slice has default_image set then use it
        if slice.default_image:
            return slice.default_image

        raise XOSProgrammingError("Please set a default image for %s" % self.slice.name)

    def save_instance(self, instance):
        # Override this function to do custom pre-save or post-save processing,
        # such as creating ports for containers.
        instance.save()

    def pick_least_loaded_instance_in_slice(self, slices, image):
        for slice in slices:
            if slice.instances.all().count() > 0:
                for instance in slice.instances.all():
                    if instance.image != image:
                        continue
                    # Pick the first instance that has lesser than 5 tenants
                    if self.count_of_tenants_of_an_instance(instance) < 5:
                        return instance
        return None

    # TODO: Ideally the tenant count for an instance should be maintained using a
    # many-to-one relationship attribute, however this model being proxy, it does
    # not permit any new attributes to be defined. Find if any better solutions
    def count_of_tenants_of_an_instance(self, instance):
        tenant_count = 0
        for tenant in self.get_tenant_objects().all():
            if tenant.get_attribute("instance_id", None) == instance.id:
                tenant_count += 1
        return tenant_count

    def manage_container(self):
        from core.models import Instance, Flavor

        if self.deleted:
            return

        if (self.instance is not None) and (self.instance.image != self.image):
            self.instance.delete()
            self.instance = None

        if self.instance is None:
            if not self.provider_service.slices.count():
                raise XOSConfigurationError("The service has no slices")

            new_instance_created = False
            instance = None
            if self.get_attribute("use_same_instance_for_multiple_tenants", default=False):
                # Find if any existing instances can be used for this tenant
                slices = self.provider_service.slices.all()
                instance = self.pick_least_loaded_instance_in_slice(slices, self.image)

            if not instance:
                slice = self.provider_service.slices.all()[0]

                flavor = slice.default_flavor
                if not flavor:
                    flavors = Flavor.objects.filter(name="m1.small")
                    if not flavors:
                        raise XOSConfigurationError("No m1.small flavor")
                    flavor = flavors[0]

                if slice.default_isolation == "container_vm":
                    (node, parent) = ContainerVmScheduler(slice).pick()
                else:
                    (node, parent) = LeastLoadedNodeScheduler(slice).pick()

                instance = Instance(slice=slice,
                                    node=node,
                                    image=self.image,
                                    creator=self.creator,
                                    deployment=node.site_deployment.deployment,
                                    flavor=flavor,
                                    isolation=slice.default_isolation,
                                    parent=parent)
                self.save_instance(instance)
                new_instance_created = True

            try:
                self.instance = instance
                super(TenantWithContainer, self).save()
            except:
                if new_instance_created:
                    instance.delete()
                raise

    def cleanup_container(self):
        if self.instance:
            if self.get_attribute("use_same_instance_for_multiple_tenants", default=False):
                # Delete the instance only if this is last tenant in that
                # instance
                tenant_count = self.count_of_tenants_of_an_instance(
                    self.instance)
                if tenant_count == 0:
                    self.instance.delete()
            else:
                self.instance.delete()
            self.instance = None

    def save(self, *args, **kwargs):
        if (not self.creator) and (hasattr(self, "caller")) and (self.caller):
            self.creator = self.caller
        super(TenantWithContainer, self).save(*args, **kwargs)


class CoarseTenant(Tenant):
    """ TODO: rename "CoarseTenant" --> "StaticTenant" """
    class Meta:
        proxy = True

    KIND = COARSE_KIND

    def save(self, *args, **kwargs):
        if (not self.subscriber_service):
            raise XOSValidationError("subscriber_service cannot be null")
        if (self.subscriber_tenant or self.subscriber_user):
            raise XOSValidationError(
                "subscriber_tenant and subscriber_user must be null")

        super(CoarseTenant, self).save()


class Subscriber(TenantRoot):
    """ Intermediate class for TenantRoots that are to be Subscribers """

    class Meta:
        proxy = True

    KIND = "Subscriber"


class Provider(TenantRoot):
    """ Intermediate class for TenantRoots that are to be Providers """

    class Meta:
        proxy = True

    KIND = "Provider"


class TenantAttribute(PlCoreBase):
    name = models.CharField(help_text="Attribute Name", max_length=128)
    value = models.TextField(help_text="Attribute Value")
    tenant = models.ForeignKey(Tenant, related_name='tenantattributes',
                               help_text="The Tenant this attribute is associated with")

    def __unicode__(self): return u'%s-%s' % (self.name, self.id)


class TenantRootRole(PlCoreBase):
    ROLE_CHOICES = (('admin', 'Admin'), ('access', 'Access'))

    role = StrippedCharField(choices=ROLE_CHOICES, unique=True, max_length=30)

    def __unicode__(self): return u'%s' % (self.role)


class TenantRootPrivilege(PlCoreBase):
    user = models.ForeignKey('User', related_name="tenant_root_privileges")
    tenant_root = models.ForeignKey(
        'TenantRoot', related_name="tenant_root_privileges")
    role = models.ForeignKey(
        'TenantRootRole', related_name="tenant_root_privileges")

    class Meta:
        unique_together = ('user', 'tenant_root', 'role')

    def __unicode__(self): return u'%s %s %s' % (
        self.tenant_root, self.user, self.role)

    def save(self, *args, **kwds):
        if not self.user.is_active:
            raise PermissionDenied, "Cannot modify role(s) of a disabled user"
        super(TenantRootPrivilege, self).save(*args, **kwds)

    def can_update(self, user):
        return user.can_update_tenant_root_privilege(self)

    @classmethod
    def select_by_user(cls, user):
        if user.is_admin:
            return cls.objects.all()
        else:
            # User can see his own privilege
            trp_ids = [trp.id for trp in cls.objects.filter(user=user)]

            # A slice admin can see the SlicePrivileges for his Slice
            for priv in cls.objects.filter(user=user, role__role="admin"):
                trp_ids.extend(
                    [trp.id for trp in cls.objects.filter(tenant_root=priv.tenant_root)])

            return cls.objects.filter(id__in=trp_ids)


class TenantRole(PlCoreBase):
    """A TenantRole option."""
    ROLE_CHOICES = (('admin', 'Admin'), ('access', 'Access'))
    role = StrippedCharField(choices=ROLE_CHOICES, unique=True, max_length=30)

    def __unicode__(self): return u'%s' % (self.role)


class TenantPrivilege(PlCoreBase):
    """"A TenantPrivilege which defines how users can access a particular Tenant.

    Attributes:
        id (models.AutoField): The ID of the privilege.
        user (models.ForeignKey): A Foreign Key to the a User.
        tenant (models.ForeignKey): A ForeignKey to the Tenant.
        role (models.ForeignKey): A ForeignKey to the TenantRole.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', related_name="tenantprivileges")
    tenant = models.ForeignKey('Tenant', related_name="tenantprivileges")
    role = models.ForeignKey('TenantRole', related_name="tenantprivileges")

    def __unicode__(self): return u'%s %s %s' % (
        self.tenant, self.user, self.role)

    def save(self, *args, **kwds):
        if not self.user.is_active:
            raise PermissionDenied, "Cannot modify role(s) of a disabled user"
        super(TenantPrivilege, self).save(*args, **kwds)

    def can_update(self, user):
        return user.can_update_tenant_privilege(self)

    @classmethod
    def select_by_user(cls, user):
        if user.is_admin:
            return cls.objects.all()
        else:
            # User can see his own privilege
            trp_ids = [trp.id for trp in cls.objects.filter(user=user)]

            # A tenant admin can see the TenantPrivileges for their Tenants
            for priv in cls.objects.filter(user=user, role__role="admin"):
                trp_ids.extend(
                    [trp.id for trp in cls.objects.filter(tenant=priv.tenant)])

            return cls.objects.filter(id__in=trp_ids)
