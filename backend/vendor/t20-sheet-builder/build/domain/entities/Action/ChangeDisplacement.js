"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeDisplacement = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class ChangeDisplacement extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'changeDisplacement' }));
    }
    execute() {
        const sheetDisplacement = this.transaction.sheet.getSheetDisplacement();
        sheetDisplacement.changeDisplacement(this.payload.displacement);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        return `${source}: deslocamento alterado para ${this.payload.displacement}m.`;
    }
}
exports.ChangeDisplacement = ChangeDisplacement;
