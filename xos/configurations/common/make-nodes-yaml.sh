FN=$SETUPDIR/nodes.yaml

rm -f $FN

cat >> $FN <<EOF
tosca_definitions_version: tosca_simple_yaml_1_0

imports:
   - custom_types/xos.yaml

description: autogenerated nodes file

topology_template:
  node_templates:
    MyDeployment:
        type: tosca.nodes.Deployment
    mysite:
        type: tosca.nodes.Site
EOF

NODES=$( bash -c "source $SETUPDIR/admin-openrc.sh ; nova host-list" |grep compute|awk '{print $2}' )
I=0
for NODE in $NODES; do
    echo $NODE
    cat >> $FN <<EOF
    $NODE:
      type: tosca.nodes.Node
      requirements:
        - site:
            node: mysite
            relationship: tosca.relationships.MemberOfSite
        - deployment:
            node: MyDeployment
            relationship: tosca.relationships.MemberOfDeployment
EOF
done
