"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeClimbingDisplacement = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class ChangeClimbingDisplacement extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'changeClimbingDisplacement' }));
    }
    execute() {
        const sheetDisplacement = this.transaction.sheet.getSheetDisplacement();
        sheetDisplacement.changeClimbingDisplacement(this.payload.climbingDisplacement);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        return `${source}: deslocamento de escalada alterado para ${this.payload.climbingDisplacement}m.`;
    }
}
exports.ChangeClimbingDisplacement = ChangeClimbingDisplacement;
