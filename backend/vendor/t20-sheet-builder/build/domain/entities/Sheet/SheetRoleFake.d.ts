import { type RoleInterface } from '../Role';
import { type SheetRoleInterface } from './SheetRoleInterface';
export declare class SheetRoleFake implements SheetRoleInterface {
    role: RoleInterface | undefined;
    chooseRole: import("vitest").Mock<any, any>;
    constructor(role?: RoleInterface | undefined);
    getRole(): RoleInterface | undefined;
}
