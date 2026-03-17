"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BecomeDevout = void 0;
const Action_1 = require("./Action");
class BecomeDevout extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'becomeDevout' }));
    }
    execute() {
        const sheetDevotion = this.transaction.sheet.getSheetDevotion();
        sheetDevotion.becomeDevout(this.payload.devotion, this.transaction);
    }
    getDescription() {
        return `Tornou-se devoto de ${this.payload.devotion.deity.name}`;
    }
}
exports.BecomeDevout = BecomeDevout;
