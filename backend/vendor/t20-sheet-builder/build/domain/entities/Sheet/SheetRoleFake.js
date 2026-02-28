"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetRoleFake = void 0;
class SheetRoleFake {
    constructor(role = undefined) {
        this.role = role;
        this.chooseRole = vi.fn();
    }
    getRole() {
        return this.role;
    }
}
exports.SheetRoleFake = SheetRoleFake;
