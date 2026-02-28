"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LearnCircle = void 0;
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class LearnCircle extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'learnCircle' }));
    }
    execute() {
        const sheetSpells = this.transaction.sheet.getSheetSpells();
        sheetSpells.learnCircle(this.payload.circle, this.payload.type, this.payload.schools);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const circle = Translator_1.Translator.getSpellCircleTranslation(this.payload.circle);
        const spellType = Translator_1.Translator.getSpellTypeTranslation(this.payload.type);
        const readableSpellType = spellType.toLowerCase().concat('s');
        return `${source}: você pode lançar magias ${readableSpellType} de ${circle} círculo`;
    }
}
exports.LearnCircle = LearnCircle;
