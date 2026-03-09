"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChooseRace = void 0;
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ChooseRace extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'chooseRace' }));
    }
    execute() {
        const sheetRace = this.transaction.sheet.getSheetRace();
        sheetRace.chooseRace(this.payload.race, this.transaction);
    }
    getDescription() {
        return `Raça escolhida: ${Translator_1.Translator.getRaceTranslation(this.payload.race.name)}.`;
    }
}
exports.ChooseRace = ChooseRace;
