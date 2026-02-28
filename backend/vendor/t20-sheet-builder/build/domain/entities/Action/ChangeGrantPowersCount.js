"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeGrantPowersCount = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class ChangeGrantPowersCount extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'changeGrantPowersCount' }));
    }
    execute() {
        const sheetDevotion = this.transaction.sheet.getSheetDevotion();
        sheetDevotion.changeGrantedPowerCount(this.payload.count);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        return `${source}: quantidade de poderes concedidos por devoção é ${this.payload.count}.`;
    }
}
exports.ChangeGrantPowersCount = ChangeGrantPowersCount;
