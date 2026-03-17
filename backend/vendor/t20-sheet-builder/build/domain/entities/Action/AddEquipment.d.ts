import { Action, type ActionSubClassParams } from './Action';
export declare class AddEquipment extends Action<'addEquipment'> {
    constructor(params: ActionSubClassParams<'addEquipment'>);
    execute(): void;
    getDescription(): string;
}
