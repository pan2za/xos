"use strict";angular.module("xos.mcord-slicing",["ngResource","ngCookies","ui.router","xos.helpers"]).config(["$stateProvider",function(e){e.state("slicing-topo",{url:"/",template:"<slicing-topo></slicing-topo>"}).state("node-links",{url:"/data",template:"<node-links></node-links>"})}]).config(["$httpProvider",function(e){e.interceptors.push("NoHyperlinks")}]).service("McordSlicingTopo",["$http","$q",function(e,t){this.query=function(){var n=t.defer();return e.get("api/service/mcord_slicing_ui/topology/").then(function(e){var t=void 0;t=e.data.hasOwnProperty("nodes")?e.data:{nodes:e.data[0],links:e.data[1]},n.resolve(t)})["catch"](function(e){n.reject(e)}),{$promise:n.promise}}}]).directive("nodeLinks",function(){return{restrict:"E",scope:{},bindToController:!0,controllerAs:"vm",templateUrl:"templates/node-links.tpl.html",controller:["McordSlicingTopo",function(e){var t=this;this.tableConfig={columns:[{label:"Id",prop:"id"},{label:"Name",prop:"name"},{label:"Type",prop:"type"},{label:"Plane",prop:"plane"},{label:"Model Id",prop:"model_id"}]},e.query().$promise.then(function(e){t.users=e.nodes})["catch"](function(e){throw new Error(e)})}]}}),angular.module("xos.mcord-slicing").run(["$templateCache",function(e){e.put("templates/node-links.tpl.html",'<div class="row">\n  <div class="col-sm-12">\n    <xos-table config="vm.tableConfig" data="vm.users"></xos-table>\n  </div>\n  <div class="col-sm-12"></div>\n</div>'),e.put("templates/slicing-topo.tpl.html","")}]);var _slicedToArray=function(){function e(e,t){var n=[],o=!0,r=!1,i=void 0;try{for(var a,s=e[Symbol.iterator]();!(o=(a=s.next()).done)&&(n.push(a.value),!t||n.length!==t);o=!0);}catch(c){r=!0,i=c}finally{try{!o&&s["return"]&&s["return"]()}finally{if(r)throw i}}return n}return function(t,n){if(Array.isArray(t))return t;if(Symbol.iterator in Object(t))return e(t,n);throw new TypeError("Invalid attempt to destructure non-iterable instance")}}();!function(){angular.module("xos.mcord-slicing").directive("slicingTopo",function(){return{restrict:"E",scope:{},bindToController:!0,controllerAs:"vm",templateUrl:"templates/slicing-topo.tpl.html",controller:["$element","SliceGraph","McordSlicingTopo","_","NodePositioner","FormHandler",function(e,t,n,o,r,i){var a=this,s=void 0,c=void 0,d=void 0,l=void 0,u=void 0,p=void 0,f=void 0,v=void 0,m=void 0,g=void 0,h=void 0,y=void 0,x=d3.transition().duration(500);this.activeSlices=[];var b=function(){v=null,m=null,f.classed("hidden",!0)};n.query().$promise.then(function(n){r.storeEl(e[0]),w(e[0]),t.buildGraph(n),k=t.positionGraph(e[0]),S=t.getGraphLinks(k),H()})["catch"](function(e){throw new Error(e)});var w=function(e){a.el=e,d3.select(e).select("svg").remove(),s=d3.select(e).append("svg").style("width",e.clientWidth+"px").style("height",e.clientHeight+"px"),u=s.append("g").attr({"class":"link-group"}),l=s.append("g").attr({"class":"node-group"}),p=d3.select(e).append("div").attr({"class":"form-container"}),f=s.append("svg:path").attr("class","dragline hidden").attr("d","M0,0L0,0")},P=function(){s.selectAll(".link").attr("x1",function(e){return e.source.x}).attr("y1",function(e){return e.source.y}).attr("x2",function(e){return e.target.x}).attr("y2",function(e){return e.target.y})},k=[],S=[],F=function(e){var n=t.getSliceDetail(e),o=_slicedToArray(n,2),r=o[0],i=o[1];k=k.concat(r),S=S.concat(i),H()},I=function(e){t.removeActiveSlice(e),h&&h.sliceId===e&&(h=null,y=null),k=o.filter(k,function(t){return t.sliceId!==e||"control"!==t.plane&&"button"!==t.type||(i.removeFormByParentNode(t,u,p),!1)}),k=o.map(k,function(t){return t.sliceId===e&&delete t.sliceId,t}),S=o.filter(S,function(e){return o.findIndex(k,{id:e.data.source})!==-1&&o.findIndex(k,{id:e.data.target})!==-1}),H()},N=function(e){console.log(S),o.remove(S,function(t){return t.data.id===e}),console.log(S),H()},A=function(e){console.log("exp",e),b();var t=["ran-ru","ran-cu","pgw","sgw"];t.indexOf(e.type)>-1&&"data"===e.plane&&!e.sliceId?F(e):"button"===e.type?I(e.sliceId):!e.formAttached&&e.model?(e.formAttached=!0,i.drawForm(e,u,p)):e.formAttached&&(e.formAttached=!1,i.removeFormByParentNode(e,u,p))},E=function(){if(h){if(y=t.getNodeSuccessors(h),0===y.length)return;h.selected=!1;var e=o.findIndex(k,{id:y[0].id});h=k[e],h.selected=!0;var n=t.getNodeSuccessors(h);y=n.lenght>0?t.getNodePredecessors(n[0]):null}else h=k[0],h.selected=!0;H()},D=function(){if(h){if(y=t.getNodePredecessors(h),0===y.length)return;h.selected=!1;var e=o.findIndex(k,{id:y[0].id});e<0&&(e=k.length-1),h=k[e],h.selected=!0}else h=k[0],h.selected=!0;H()},C=function(e,t){return e.y<t.y?1:e.y>t.y?-1:0},$=function(e){return o.filter(k,function(t){return"pgw"===e.type&&"button"===t.type||("button"===e.type&&"pgw"===t.type||("sgw"===e.type&&"mme"===t.type||("mme"===e.type&&"sgw"===t.type||t.type===e.type)))}).sort(C)},G=function(){if(h){h.selected=!1;var e=$(h),t=o.findIndex(e,{id:h.id})+1;t===e.length&&(t=0);var n=o.findIndex(k,{id:e[t].id});h=k[n],h.selected=!0}else h=k[0],h.selected=!0;H()},O=function(){if(h){h.selected=!1;var e=$(h),t=o.findIndex(e,{id:h.id})-1;t<0&&(t=e.length-1);var n=o.findIndex(k,{id:e[t].id});h=k[n],h.selected=!0}else h=k[0],h.selected=!0;H()},H=function L(){d3.layout.force().nodes(k).links(S).charge(-1060).gravity(.1).linkDistance(200).size([a.el.clientWidth,a.el.clientHeight]).on("tick",P).start();d=u.selectAll(".link-container").data(S,function(e){return e.data.id}).enter().insert("g").attr({"class":"link-container",opacity:0}),d.transition(x).attr({opacity:1}),d.insert("line").attr("class",function(e){return"link "+e.data.plane}).on("click",function(e){g=e,d3.selectAll(".link").classed("selected",!1),d3.select(this).classed("selected",!0)}),c=l.selectAll(".node").data(k,function(e){return e.id}).attr({"class":function(e){return"node "+e.plane+" "+e.type+" "+(e.selected?"selected":"")}}),c.enter().append("g").attr({"class":"node-container",transform:function(e){return e.transform},opacity:0}),c.transition(x).attr({opacity:1}),c.append("rect").attr({"class":function(e){return"node "+e.plane+" "+e.type+" "+(e.selected?"selected":"")},width:100,height:50,x:-50,y:-25}),c.append("text").attr({"text-anchor":"middle","alignment-baseline":"middle"}).text(function(e){return""+e.name}),c.on("click",function(e){A(e)}),c.on("mousedown",function(e){v=e,f.classed("hidden",!1).attr("d","M"+v.x+","+v.y+"L"+v.x+","+v.y)}).on("mouseover",function(e){v&&(m=e)}),s.on("mousemove",function(){v&&f.attr("d","M"+v.x+","+v.y+"L"+d3.mouse(this)[0]+","+d3.mouse(this)[1])}).on("mouseup",function(){if(!v||!m)return void b();var e=t.getNodeDataPlaneSuccessors(v)[0].type;return m.type!==e?void b():(S.push({source:v,target:m,data:{id:v.id+"."+m.id,source:v.id,target:m.id}}),L(),void b())}),s.selectAll(".node-container").data(k,function(e){return e.id}).exit().transition(x).attr({opacity:0}).remove(),s.selectAll(".link-container").data(S,function(e){return e.data.id}).exit().transition(x).attr({opacity:0}).remove()};d3.select("body").on("keydown",function(){"Backspace"===d3.event.code&&g&&N(g.data.id),"Enter"===d3.event.code&&h&&(d3.event.preventDefault(),A(h)),"Escape"===d3.event.code&&h&&(h.selected=!1,h=null,y=null,H()),"ArrowRight"===d3.event.code&&(d3.event.preventDefault(),E()),"ArrowLeft"===d3.event.code&&(d3.event.preventDefault(),D()),"ArrowUp"===d3.event.code&&(d3.event.preventDefault(),G()),"ArrowDown"===d3.event.code&&(d3.event.preventDefault(),O())})}]}})}(),function(){angular.module("xos.mcord-slicing").service("SliceGraph",["_","NodePositioner",function(e,t){var n=this,o=new graphlib.Graph;this.buildGraph=function(t){e.forEach(t.nodes,function(e){return o.setNode(e.id,e)}),e.forEach(t.links,function(e){return o.setEdge(e.source,e.target,e)})},this.getLinks=function(){return o.edges().map(function(e){return{source:o.node(e.v),target:o.node(e.w),data:o.edge(e)}})},this.getGraph=function(){return o},this.getNodeSuccessors=function(t){return e.map(o.successors(t.id),function(e){return o.node(e)})},this.getNodePredecessors=function(t){return e.map(o.predecessors(t.id),function(e){return o.node(e)})},this.getNodeDataPlaneSuccessors=function(t){return e.filter(n.getNodeSuccessors(t),function(e){return"data"===e.plane})},this.getUpstreamSinks=function(t){var n=e.reduce(o.sinks(),function(e,t,n){var r=o.node(t);return"upstream"===r.type&&e.push(r),e},[]);return e.map(n,function(e,o){return e.position={top:0,bottom:t.clientHeight,total:n.length,index:o+1},e})},this.positionGraph=function(o){var r=n.getUpstreamSinks(o),i=[];return e.forEach(r,function(e,t){i=i.concat(n.findPredecessor(e))}),r=r.concat(i),r=e.map(r,function(e){return t.getDataPlaneNodePos(e,o)})},this.findPredecessor=function(r){var i=o.predecessors(r.id);i=i.map(function(e,n){e=o.node(e);var a=(r.position.bottom-r.position.top)/r.position.total,s=t.getVpos(r);return e.position={top:s-a/2,bottom:s+a/2,total:i.length,index:n+1},e});var a=e.reduce(i,function(e,t){return e.concat(n.findPredecessor(t))},[]);return i.concat(a)},this.getGraphLinks=function(t){var n=[];return e.forEach(t,function(t){var r=o.inEdges(t.id);e.forEach(r,function(e){n.push({source:o.node(e.v),target:o.node(e.w),data:o.edge(e)})})}),n},this.getDataPlaneForSlice=function(e,t){var n=o.node(o.successors(e.id)[0]),r=o.node(o.successors(n.id)[0]),i=o.node(o.successors(r.id)[0]);return e.sliceId=t,n.sliceId=t,r.sliceId=t,i.sliceId=t,[e,n,r,i]},this.getControlPlaneForSlice=function(n,r){return e.reduce(n,function(e,n){var i=o.node(o.successors(n.id)[1]);if(i=t.getControlPlaneNodePos(i,n),i.sliceId=r,"sgw"===i.type){var a=o.node(o.successors(i.id)[1]);a=t.getControlPlaneNodePos(a,i),a.sliceId=r,e.push(a)}return e.concat(i)},[])},this.activeSlices=[],this.getSliceDetail=function(r){if(r.sliceId&&n.activeSlices.indexOf(r.sliceId)>-1)return[[],[]];var i=e.min(n.activeSlices)?e.min(n.activeSlices)+1:1;n.activeSlices.push(i);var a=function(e){for(var t=!0;t;){var n=e;if(t=!1,"ran-ru"===n.type)return n;var r=o.predecessors(n.id);e=o.node(r[0]),t=!0,r=void 0}}(r),s=n.getDataPlaneForSlice(a,i),c=n.getControlPlaneForSlice(s,i),d=n.getGraphLinks(c),l={name:"Close",id:"close-button-"+i,type:"button",sliceId:i};return l=t.getControlPlaneNodePos(l,c[3]),c.push(l),[c,d]},this.removeActiveSlice=function(e){n.activeSlices.splice(n.activeSlices.indexOf(e),1)}}]).service("NodePositioner",["_","sliceElOrder",function(e,t){var n=this,o=void 0;this.storeEl=function(e){o=e},this.getHpos=function(e,n){var o=t.indexOf(e.type)+1;"mme"===e.type&&(o=t.indexOf("sgw")+1),"button"===e.type&&(o=t.indexOf("pgw")+1);var r=n.clientWidth/(t.length+1)*o;return r},this.getVpos=function(e){var t=e.position.bottom-e.position.top,n=t/(e.position.total+1),o=n*e.position.index+e.position.top;return o},this.getDataPlaneNodePos=function(e){var t=n.getHpos(e,o),r=n.getVpos(e);return e.x=t,e.y=r,e.transform="translate("+t+", "+r+")",e.fixed=!0,e},this.getControlPlaneNodePos=function(e,t){var r=n.getHpos(e,o),i=t.y-75;return e.x=r,e.y=i,e.transform="translate("+r+", "+i+")",e.fixed=!0,e}}]).value("sliceElOrder",["ue","profile","ran-ru","ran-cu","sgw","pgw","upstream"])}(),function(){angular.module("xos.mcord-slicing").service("FormHandler",["LabelFormatter","XosFormHelpers",function(e,t){var n=this,o=this,r=d3.transition().duration(500);this.drawForm=function(e,t,i){var a=t.append("line").attr({"class":"form-line",id:"form-line-"+e.type+"-"+e.id,x1:e.x+10,y1:e.y,x2:e.x+10,y2:e.y+40,opacity:0});a.transition(r).attr({opacity:1});var s=i.append("div").attr({"class":"element-form",id:"form-"+e.type+"-"+e.id}).style({opacity:0}),c=s.append("form");n.addFormfields(e,c);var d=c.append("div").attr({"class":"row"});d.append("div").attr({"class":"col-xs-6"}).append("a").attr({"class":"btn btn-danger","data-parent-node-type":e.type,"data-parent-node-id":e.id}).text("Close").on("click",function(){o.removeForm(d3.select(this).attr("data-parent-node-type"),d3.select(this).attr("data-parent-node-id"),t,i)}),d.append("div").attr({"class":"col-xs-6"}).append("button").attr({type:"button","class":"btn btn-success"}).text("Save").on("click",function(){$("#form-"+e.type+"-"+e.id+" input").each(function(){var e=$(this),t=e.val(),n=e.attr("name");console.log(n,t)})}),s.transition(r).style({opacity:1,top:e.y+95+"px",left:e.x+"px"})},this.removeForm=function(e,t,o,r){n.removeFormByParentNode({type:e,id:t},o,r)},this.removeFormByParentNode=function(e,t,n){n.selectAll("#form-"+e.type+"-"+e.id).transition(r).style({opacity:0}).remove(),t.selectAll("#form-line-"+e.type+"-"+e.id).transition(r).attr({opacity:0}).remove()},this.getFieldValue=function(e,t){return"date"===t&&(e=new Date(e),e=e.getFullYear()+"-"+("0"+e.getMonth()+1).slice(-2)+"-"+("0"+e.getDate()).slice(-2)),e||""},this.addFormField=function(o,r,i){var a=t._getFieldFormat(r);i.append("div").attr({"class":"row"}).append("div").attr({"class":"col-xs-12"}).append("label").text(o?e.format(o):"test").append("input").attr({type:a,name:o,value:n.getFieldValue(r,a),"class":"form-control"})},this.addFormfields=function(e,t){if(n.addFormField("name",e.name,t),!e.model)return n.addFormField(null,null,t);var o=Object.keys(e.model);_.forEach(o,function(o){n.addFormField(o,e.model[o],t)})}}])}(),angular.module("xos.mcord-slicing").run(["$location",function(e){e.path("/")}]);
