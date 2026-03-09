import { type RoleInterface } from '../../Role';
import { type SheetRoleInterface } from '../SheetRoleInterface';
export declare class CharacterSheetRole implements SheetRoleInterface {
    private readonly role;
    constructor(role: RoleInterface);
    getRole(): RoleInterface;
}
