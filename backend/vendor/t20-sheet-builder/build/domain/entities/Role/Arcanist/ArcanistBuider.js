"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistBuilder = void 0;
const Arcanist_1 = require("./Arcanist");
class ArcanistBuilder {
    static chooseSkills(skills) {
        return {
            choosePath: (path) => ArcanistBuilder.choosePath(path, skills),
        };
    }
    static choosePath(path, skills) {
        return {
            chooseSpells: (spells) => ArcanistBuilder.chooseSpells(skills, path, spells),
        };
    }
    static chooseSpells(skills, path, spells) {
        return new Arcanist_1.Arcanist(skills, path, spells);
    }
}
exports.ArcanistBuilder = ArcanistBuilder;
