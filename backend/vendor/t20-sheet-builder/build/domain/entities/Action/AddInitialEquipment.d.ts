import { Action, type ActionSubClassParams } from './Action';
export declare class AddInitialEquipment extends Action<'addInitialEquipment'> {
    constructor(params: ActionSubClassParams<'addInitialEquipment'>);
    execute(): void;
    getDescription(): string;
}
