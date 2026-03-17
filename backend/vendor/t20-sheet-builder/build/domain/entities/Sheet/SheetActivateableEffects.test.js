"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Role_1 = require("../Role");
const PreyMarkEffect_1 = require("../Role/Ranger/PreyMark/PreyMarkEffect");
const SheetActivateableEffects_1 = require("./SheetActivateableEffects");
describe('SheetActivatebleEffects', () => {
    it('should init with empty list', () => {
        const effects = new SheetActivateableEffects_1.SheetActivateableEffects();
        expect(effects.getEffects()).toEqual(new Map());
    });
    it('should add effect', () => {
        const effects = new SheetActivateableEffects_1.SheetActivateableEffects();
        const preyMarkEffect = new PreyMarkEffect_1.PreyMarkEffect();
        effects.register(preyMarkEffect);
        expect(effects.getEffects()).toEqual(new Map([
            [Role_1.RoleAbilityName.preyMark, preyMarkEffect],
        ]));
    });
});
