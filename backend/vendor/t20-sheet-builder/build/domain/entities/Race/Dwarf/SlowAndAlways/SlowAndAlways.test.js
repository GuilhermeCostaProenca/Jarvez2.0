"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Sheet_1 = require("../../../Sheet");
const Transaction_1 = require("../../../Sheet/Transaction");
const SlowAndAlways_1 = require("./SlowAndAlways");
describe('SlowAndAlways', () => {
    it('should dispatch displacement change', () => {
        const slowAndAlways = new SlowAndAlways_1.SlowAndAlways();
        const sheet = new Sheet_1.BuildingSheet();
        const transaction = new Transaction_1.Transaction(sheet);
        slowAndAlways.addToSheet(transaction);
        expect(sheet.getSheetDisplacement().getDisplacement()).toBe(6);
    });
});
