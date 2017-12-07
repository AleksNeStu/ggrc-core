/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Component from '../instance-acl-diff';

describe('instance-acl-diff component', () => {
  let viewModel;

  beforeAll(()=> {
    viewModel = getComponentVM(Component);
  });

  describe('"getEmailsOrEmpty" method', () => {
    let getEmailsOrEmpty;
    let emptyValue;

    beforeAll(() => {
      emptyValue = viewModel.attr('emptyValue');
      getEmailsOrEmpty = viewModel.getEmailsOrEmpty.bind(viewModel);
    });

    it('shoud return emptyValue. argument is undefined', () => {
      const result = getEmailsOrEmpty();
      expect(result.length).toBe(1);
      expect(result[0]).toEqual(emptyValue);
    });

    it('shoud return emptyValue. argument is empry array', () => {
      const result = getEmailsOrEmpty([]);
      expect(result.length).toBe(1);
      expect(result[0]).toEqual(emptyValue);
    });

    it('shoud return sorted emails', () => {
      const values = [
        {id: 5, email: 'sona@gg.com'},
        {id: 3, email: 'zed@gg.com'},
        {id: 15, email: 'leona@gg.com'},
      ];
      const result = getEmailsOrEmpty(values);
      expect(result.length).toBe(3);
      expect(result[0]).toEqual(values[2].email);
      expect(result[1]).toEqual(values[0].email);
      expect(result[2]).toEqual(values[1].email);
    });
  });
});
