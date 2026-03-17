"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleFactory = void 0;
const RoleSerializedHandlerArcanist_1 = require("./RoleHandler/RoleSerializedHandlerArcanist");
const RoleSerializedHandlerWarrior_1 = require("./RoleHandler/RoleSerializedHandlerWarrior");
class RoleFactory {
    static makeFromSerialized(serialized) {
        const warrior = new RoleSerializedHandlerWarrior_1.RoleSerializedHandlerWarrior();
        const arcanist = new RoleSerializedHandlerArcanist_1.RoleSerializedHandlerArcanist();
        warrior
            .setNext(arcanist);
        return warrior.execute(serialized);
    }
}
exports.RoleFactory = RoleFactory;
