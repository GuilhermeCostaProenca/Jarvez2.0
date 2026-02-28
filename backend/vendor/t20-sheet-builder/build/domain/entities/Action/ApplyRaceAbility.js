"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApplyRaceAbility = void 0;
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ApplyRaceAbility extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'applyRaceAbility' }));
    }
    execute() {
        const sheetAbilities = this.transaction.sheet.getSheetAbilities();
        sheetAbilities.applyRaceAbility(this.payload.ability, this.transaction, this.payload.source);
    }
    getDescription() {
        const ability = Translator_1.Translator.getRaceAbilityTranslation(this.payload.ability.name);
        return `Habilidade de raça: ${ability} adicionada.`;
    }
}
exports.ApplyRaceAbility = ApplyRaceAbility;
