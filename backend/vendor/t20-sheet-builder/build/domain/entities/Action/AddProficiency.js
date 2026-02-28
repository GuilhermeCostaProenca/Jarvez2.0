"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddProficiency = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddProficiency extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addProficiency' }));
    }
    execute() {
        const sheetProficiencies = this.transaction.sheet.getSheetProficiencies();
        sheetProficiencies.addProficiency(this.payload.proficiency);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const proficiency = new Translatable_1.Translatable(this.payload.proficiency);
        return `${source}: você é proficiente com ${proficiency.getTranslation()}.`;
    }
}
exports.AddProficiency = AddProficiency;
