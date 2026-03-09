"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LearnSpell = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class LearnSpell extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'learnSpell' }));
    }
    execute() {
        const sheetSpells = this.transaction.sheet.getSheetSpells();
        sheetSpells.learnSpell(this.payload.spell, this.payload.needsCircle, this.payload.needsSchool);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const spell = new Translatable_1.Translatable(this.payload.spell.name).getTranslation();
        return `${source}: você aprendeu a magia ${spell}.`;
    }
}
exports.LearnSpell = LearnSpell;
