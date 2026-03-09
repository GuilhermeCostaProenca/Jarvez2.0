"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApplyRoleAbility = void 0;
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ApplyRoleAbility extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'applyRoleAbility' }));
    }
    execute() {
        const sheetAbilities = this.transaction.sheet.getSheetAbilities();
        sheetAbilities.applyRoleAbility(this.payload.ability, this.transaction, this.payload.source);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const ability = Translator_1.Translator.getRoleAbilityTranslation(this.payload.ability.name);
        return `${source}: habilidade ${ability} adicionada.`;
    }
}
exports.ApplyRoleAbility = ApplyRoleAbility;
