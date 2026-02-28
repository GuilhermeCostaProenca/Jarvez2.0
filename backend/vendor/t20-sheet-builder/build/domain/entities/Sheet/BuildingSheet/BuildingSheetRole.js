"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BuildingSheetRole = void 0;
class BuildingSheetRole {
    constructor(role = undefined) {
        this.role = role;
    }
    chooseRole(role, transaction) {
        this.role = role;
        this.role.addToSheet(transaction);
    }
    getRole() {
        return this.role;
    }
}
exports.BuildingSheetRole = BuildingSheetRole;
