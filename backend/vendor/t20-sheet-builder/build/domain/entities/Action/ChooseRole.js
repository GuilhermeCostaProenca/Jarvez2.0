"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChooseRole = void 0;
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ChooseRole extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'chooseRole' }));
    }
    execute() {
        const sheetRole = this.transaction.sheet.getSheetRole();
        sheetRole.chooseRole(this.payload.role, this.transaction);
    }
    getDescription() {
        const role = Translator_1.Translator.getRoleTranslation(this.payload.role.name);
        const { initialLifePoints, manaPerLevel } = this.payload.role;
        const initialSkills = this.payload.role.getTotalInitialSkills();
        return `Classe escolhida: ${role}. ${initialLifePoints} PV, ${manaPerLevel} PM e ${initialSkills} perícias iniciais.`;
    }
}
exports.ChooseRole = ChooseRole;
