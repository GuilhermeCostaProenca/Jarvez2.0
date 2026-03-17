"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleAbilitiesPerLevelFactory = void 0;
const Sheet_1 = require("../Sheet");
class RoleAbilitiesPerLevelFactory {
    static make(abilities) {
        return Object.assign({ [Sheet_1.Level.one]: {}, [Sheet_1.Level.two]: {}, [Sheet_1.Level.three]: {}, [Sheet_1.Level.four]: {}, [Sheet_1.Level.five]: {}, [Sheet_1.Level.six]: {}, [Sheet_1.Level.seven]: {}, [Sheet_1.Level.eight]: {}, [Sheet_1.Level.nine]: {}, [Sheet_1.Level.ten]: {}, [Sheet_1.Level.eleven]: {}, [Sheet_1.Level.twelve]: {}, [Sheet_1.Level.thirteen]: {}, [Sheet_1.Level.fourteen]: {}, [Sheet_1.Level.fifteen]: {}, [Sheet_1.Level.sixteen]: {}, [Sheet_1.Level.seventeen]: {}, [Sheet_1.Level.eighteen]: {}, [Sheet_1.Level.nineteen]: {}, [Sheet_1.Level.twenty]: {} }, abilities);
    }
}
exports.RoleAbilitiesPerLevelFactory = RoleAbilitiesPerLevelFactory;
