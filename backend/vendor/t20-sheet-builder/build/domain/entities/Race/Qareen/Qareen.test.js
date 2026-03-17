"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Qareen_1 = require("./Qareen");
const RaceAbilityName_1 = require("../RaceAbilityName");
const Spell_1 = require("../../Spell");
(0, vitest_1.describe)('Qareen', () => {
    let sheet;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        const qareen = new Qareen_1.Qareen('water', Spell_1.SpellName.arcaneArmor);
        const builder = new SheetBuilder_1.SheetBuilder(sheet);
        builder.chooseRace(qareen);
    });
    (0, vitest_1.it)('should apply +2 to charisma, +1 to intelligence and -1 to wisdom', () => {
        const attributes = sheet.getSheetAttributes().getValues();
        (0, vitest_1.expect)(attributes.strength).toBe(0);
        (0, vitest_1.expect)(attributes.dexterity).toBe(0);
        (0, vitest_1.expect)(attributes.constitution).toBe(0);
        (0, vitest_1.expect)(attributes.intelligence).toBe(1);
        (0, vitest_1.expect)(attributes.wisdom).toBe(-1);
        (0, vitest_1.expect)(attributes.charisma).toBe(2);
    });
    (0, vitest_1.it)('should have desires hability', () => {
        const desires = sheet
            .getSheetAbilities()
            .getRaceAbilities()
            .get(RaceAbilityName_1.RaceAbilityName.desires);
        (0, vitest_1.expect)(desires).toBeDefined();
        (0, vitest_1.expect)(desires === null || desires === void 0 ? void 0 : desires.effects.roleplay.default.description).toBe('Se lançar uma magia que alguém tenha'
            + ' pedido desde seu último turno, o custo da magia'
            + ' diminui em –1 PM. Fazer um desejo ao qareen é uma'
            + ' ação livre.');
    });
    (0, vitest_1.it)('should have elemental resistance', () => {
        var _a;
        const elementalResistance = sheet
            .getSheetAbilities()
            .getRaceAbilities()
            .get(RaceAbilityName_1.RaceAbilityName.elementalResistance);
        (0, vitest_1.expect)(elementalResistance).toBeDefined();
        (0, vitest_1.expect)(elementalResistance === null || elementalResistance === void 0 ? void 0 : elementalResistance.effects.passive.default.description).toBe('Conforme sua'
            + ' ascendência, você recebe redução 10 a um tipo de'
            + ' dano. Escolha uma: frio (qareen da água), eletricidade'
            + ' (do ar), fogo (do fogo), ácido (da terra), luz (da'
            + ' luz) ou trevas (qareen das trevas).');
        const attributes = sheet.getSheetAttributes().getValues();
        (0, vitest_1.expect)((_a = sheet.getSheetResistences().getResistances().cold) === null || _a === void 0 ? void 0 : _a.getTotal(attributes)).toBe(10);
    });
    (0, vitest_1.it)('should have mystic tattoo', () => {
        const mysticTattoo = sheet
            .getSheetAbilities()
            .getRaceAbilities()
            .get(RaceAbilityName_1.RaceAbilityName.mysticTattoo);
        (0, vitest_1.expect)(mysticTattoo).toBeDefined();
        (0, vitest_1.expect)(mysticTattoo === null || mysticTattoo === void 0 ? void 0 : mysticTattoo.effects.passive.default.description).toBe('Você'
            + ' pode lançar uma magia de 1º'
            + ' círculo a sua escolha (atributo-'
            + ' chave Carisma). Caso'
            + ' aprenda novamente essa'
            + ' magia, seu custo diminui'
            + ' em –1 PM.');
        (0, vitest_1.expect)(sheet.getSheetSpells().getSpells().get(Spell_1.SpellName.arcaneArmor)).toBeDefined();
    });
});
