import { type RoleInterface } from '../../Role';
import { type SheetRoleInterface } from '../SheetRoleInterface';
import { type TransactionInterface } from '../TransactionInterface';
export declare class BuildingSheetRole implements SheetRoleInterface {
    private role;
    constructor(role?: RoleInterface | undefined);
    chooseRole(role: RoleInterface, transaction: TransactionInterface): void;
    getRole(): RoleInterface | undefined;
}
