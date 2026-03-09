"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Minotaur = void 0;
const Race_1 = require("../Race");
const RaceName_1 = require("../RaceName");
const FearOfHeights_1 = require("./FearOfHeights");
const Hornes_1 = require("./Hornes");
const Nose_1 = require("./Nose");
const StiffLeather_1 = require("./StiffLeather");
class Minotaur extends Race_1.Race {
    constructor() {
        super(RaceName_1.RaceName.minotaur);
        this.attributeModifiers = Minotaur.attributeModifiers;
        this.abilities = {
            hornes: new Hornes_1.Hornes(),
            stiffLeather: new StiffLeather_1.StiffLeather(),
            nose: new Nose_1.Nose(),
            fearOfHeights: new FearOfHeights_1.FearOfHeights(),
        };
    }
    serializeSpecific() {
        return {
            name: Minotaur.raceName,
        };
    }
}
exports.Minotaur = Minotaur;
Minotaur.attributeModifiers = {
    strength: 2,
    constitution: 1,
    wisdom: -1,
};
Minotaur.raceName = RaceName_1.RaceName.minotaur;
