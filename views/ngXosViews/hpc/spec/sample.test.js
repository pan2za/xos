'use strict';

describe('The Hpc View', () => {
  
  var scope, element, isolatedScope, httpBackend;

  beforeEach(module('xos.hpc'));
  beforeEach(module('templates'));

  beforeEach(inject(function($httpBackend, $compile, $rootScope){

    scope = $rootScope.$new();
    element = angular.element('<hpcs-list></hpcs-list>');
    $compile(element)(scope);
    scope.$digest();
    isolatedScope = element.isolateScope().vm;
  }));

  it('should define 2 tables', () => {
    expect(isolatedScope.routerConfig).toBeDefined();
    expect(isolatedScope.cacheConfig).toBeDefined();
  });

});