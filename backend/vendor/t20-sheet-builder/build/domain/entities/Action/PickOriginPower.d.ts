import { Action, type ActionSubClassParams } from './Action';
export declare class PickOriginPower extends Action<'pickOriginPower'> {
    constructor(params: ActionSubClassParams<'pickOriginPower'>);
    execute(): void;
    getDescription(): string;
}
